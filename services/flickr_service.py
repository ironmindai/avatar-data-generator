"""
Flickr Image Search and Download Service

This module provides production-ready Flickr API integration for searching and downloading
images for the Image Datasets feature.

Key Features:
- Search photos with keyword and license filtering
- Filter out already-used photos from database
- Batch download with concurrency
- Rate limiting (3600 requests/hour max)
- Full metadata retrieval
"""

import requests
import time
import logging
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

from models import db, DatasetImage

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Flickr API Configuration
API_KEY = "1976df84b867a296ff55789ed9a4342c"
API_SECRET = "db376036a648f9c0"
FLICKR_API_BASE = "https://api.flickr.com/services/rest/"

# Rate limiting configuration
REQUEST_DELAY = 1.0  # 1 second between requests (allows 3600 requests/hour)
MAX_REQUESTS_PER_HOUR = 3600

# License mappings for readable names
LICENSE_NAMES = {
    '0': 'All Rights Reserved',
    '1': 'CC BY-NC-SA 2.0',
    '2': 'CC BY-NC 2.0',
    '3': 'CC BY-NC-ND 2.0',
    '4': 'CC BY 2.0',
    '5': 'CC BY-SA 2.0',
    '6': 'CC BY-ND 2.0',
    '7': 'No known copyright restrictions',
    '8': 'United States Government Work',
    '9': 'CC0 1.0',
    '10': 'Public Domain Mark 1.0'
}


class RateLimiter:
    """Simple rate limiter to respect Flickr API limits."""

    def __init__(self, delay: float):
        """
        Initialize rate limiter.

        Args:
            delay: Minimum seconds between requests
        """
        self.delay = delay
        self.last_request = 0

    def wait(self) -> None:
        """Wait if necessary to respect rate limit."""
        now = time.time()
        elapsed = now - self.last_request
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self.last_request = time.time()


# Global rate limiter instance
rate_limiter = RateLimiter(REQUEST_DELAY)


def _get_used_flickr_photo_ids() -> set:
    """
    Query database to get all Flickr photo IDs that have already been used.

    Returns:
        Set of Flickr photo IDs (strings) that are already in dataset_images
    """
    try:
        # Query all dataset images with source_type='flickr'
        used_images = DatasetImage.query.filter_by(source_type='flickr').all()

        # Extract source_id (Flickr photo ID) from each record
        used_ids = {img.source_id for img in used_images if img.source_id}

        logger.debug(f"Found {len(used_ids)} already-used Flickr photo IDs in database")
        return used_ids

    except Exception as e:
        logger.error(f"Error querying used Flickr photos: {e}", exc_info=True)
        # Return empty set on error to avoid blocking search
        return set()


def search_photos(
    keyword: str,
    per_page: int = 100,
    page: int = 1,
    exclude_used: bool = False,
    license_filter: Optional[str] = None
) -> Dict:
    """
    Search Flickr for photos with simple filtering.

    Args:
        keyword: Search keyword/phrase (e.g., "coffee shop interior")
        per_page: Number of results per page (max 100)
        page: Page number to retrieve (1-indexed)
        exclude_used: If True, exclude photos already in dataset_images table
        license_filter: License type filter ('cc' for Creative Commons only, None for any)

    Returns:
        Dict containing:
            - 'photos': List of photo dicts with metadata
            - 'total': Total number of matching photos available
            - 'page': Current page number
            - 'pages': Total number of pages available
            - 'per_page': Results per page

    Example:
        >>> results = search_photos("coffee shop interior", per_page=50, license_filter='cc')
        >>> for photo in results['photos']:
        ...     print(f"{photo['title']}: {photo['license']}")
    """
    try:
        # Rate limiting
        rate_limiter.wait()

        logger.info(f"Searching Flickr: '{keyword}' (page {page}, per_page {per_page}, license_filter={license_filter})")

        # Build API request parameters
        params = {
            'method': 'flickr.photos.search',
            'api_key': API_KEY,
            'text': keyword,
            'per_page': min(per_page, 100),  # Cap at 100 for UI simplicity
            'page': page,
            'format': 'json',
            'nojsoncallback': 1,
            'extras': 'url_o,url_l,url_m,description,tags,owner_name,license,date_taken,views',
            'sort': 'relevance',
            'content_type': 1,  # Photos only
            'media': 'photos',
            'min_taken_date': '2015-01-01',  # Recent photos only
        }

        # Apply license filter
        if license_filter == 'cc':
            # Creative Commons licenses only (1-6, 9, 10)
            params['license'] = '1,2,3,4,5,6,9,10'
        # If None, search all licenses (no license param = all)

        # Make API request
        response = requests.get(FLICKR_API_BASE, params=params)
        response.raise_for_status()
        result = response.json()

        if result.get('stat') != 'ok':
            logger.error(f"Flickr API error: {result}")
            raise Exception(f"Flickr API returned error: {result.get('message', 'Unknown error')}")

        photos = result['photos']['photo']
        total = result['photos']['total']
        pages = result['photos']['pages']

        logger.info(f"Flickr API returned {len(photos)} photos (total available: {total})")

        # Get already-used photo IDs if exclusion is enabled
        used_ids = _get_used_flickr_photo_ids() if exclude_used else set()
        if exclude_used:
            logger.info(f"Already-used photo IDs to exclude: {len(used_ids)} photos")

        # Filter out already-used photos
        filtered_photos = []
        excluded_used_count = 0

        for photo in photos:
            # Exclude if already used
            if exclude_used and photo['id'] in used_ids:
                excluded_used_count += 1
                logger.debug(f"Skipping already-used photo ID: {photo['id']}")
                continue

            # Add readable license name
            license_id = str(photo.get('license', '0'))
            photo['license_name'] = LICENSE_NAMES.get(license_id, 'Unknown')

            # Convert tags string to array for frontend
            tags_str = photo.get('tags', '')
            if tags_str and isinstance(tags_str, str):
                photo['tags'] = tags_str.split()  # Split space-separated tags into array
            else:
                photo['tags'] = []

            filtered_photos.append(photo)

        # Summary logging
        logger.info(f"Flickr search results for keyword='{keyword}':")
        logger.info(f"  - API returned: {len(photos)} photos")
        logger.info(f"  - Excluded (already used): {excluded_used_count} photos")
        logger.info(f"  - Final result: {len(filtered_photos)} photos")

        return {
            'photos': filtered_photos,
            'total': total,
            'page': page,
            'pages': pages,
            'per_page': per_page
        }

    except requests.RequestException as e:
        logger.error(f"Flickr API request failed: {e}", exc_info=True)
        raise Exception(f"Failed to search Flickr: {str(e)}")

    except Exception as e:
        logger.error(f"Error searching Flickr photos: {e}", exc_info=True)
        raise


def get_photo_details(photo_id: str) -> Dict:
    """
    Get full metadata for a single Flickr photo.

    Retrieves detailed information including full description, tags, license,
    owner info, and all available image URLs.

    Args:
        photo_id: Flickr photo ID

    Returns:
        Dict containing full photo metadata from Flickr API

    Raises:
        Exception: If API request fails or photo not found
    """
    try:
        # Rate limiting
        rate_limiter.wait()

        logger.debug(f"Fetching details for Flickr photo ID: {photo_id}")

        # Get photo info
        params = {
            'method': 'flickr.photos.getInfo',
            'api_key': API_KEY,
            'photo_id': photo_id,
            'format': 'json',
            'nojsoncallback': 1,
        }

        response = requests.get(FLICKR_API_BASE, params=params)
        response.raise_for_status()
        result = response.json()

        if result.get('stat') != 'ok':
            logger.error(f"Flickr API error for photo {photo_id}: {result}")
            raise Exception(f"Flickr API error: {result.get('message', 'Unknown error')}")

        photo_info = result['photo']
        logger.debug(f"Retrieved details for photo {photo_id}: {photo_info.get('title', {}).get('_content', 'Untitled')}")

        return photo_info

    except requests.RequestException as e:
        logger.error(f"Flickr API request failed for photo {photo_id}: {e}", exc_info=True)
        raise Exception(f"Failed to get photo details: {str(e)}")

    except Exception as e:
        logger.error(f"Error getting photo details for {photo_id}: {e}", exc_info=True)
        raise


def get_photo_sizes(photo_id: str) -> Dict:
    """
    Get available image sizes/URLs for a Flickr photo.

    Retrieves all available image sizes and their URLs using flickr.photos.getSizes API.

    Args:
        photo_id: Flickr photo ID

    Returns:
        Dict containing lists of sizes with 'label', 'width', 'height', 'source', 'url'.
        Includes convenience keys 'url_o' (original), 'url_l' (large), 'url_m' (medium).

    Raises:
        Exception: If API request fails or photo not found
    """
    try:
        # Rate limiting
        rate_limiter.wait()

        logger.debug(f"Fetching sizes for Flickr photo ID: {photo_id}")

        # Get photo sizes
        params = {
            'method': 'flickr.photos.getSizes',
            'api_key': API_KEY,
            'photo_id': photo_id,
            'format': 'json',
            'nojsoncallback': 1,
        }

        response = requests.get(FLICKR_API_BASE, params=params)
        response.raise_for_status()
        result = response.json()

        if result.get('stat') != 'ok':
            logger.error(f"Flickr API error for photo {photo_id} sizes: {result}")
            raise Exception(f"Flickr API error: {result.get('message', 'Unknown error')}")

        sizes = result['sizes']['size']

        # Build convenience dict with common size URLs
        sizes_dict = {'sizes': sizes}

        # Map common size labels to convenience keys
        for size in sizes:
            label = size.get('label', '')
            source = size.get('source', '')

            if label == 'Original':
                sizes_dict['url_o'] = source
            elif label == 'Large' or label == 'Large 2048':
                if 'url_l' not in sizes_dict:  # Prefer first large size
                    sizes_dict['url_l'] = source
            elif label == 'Medium' or label == 'Medium 800':
                if 'url_m' not in sizes_dict:  # Prefer first medium size
                    sizes_dict['url_m'] = source

        logger.debug(f"Retrieved {len(sizes)} sizes for photo {photo_id}")
        return sizes_dict

    except requests.RequestException as e:
        logger.error(f"Flickr API request failed for photo {photo_id} sizes: {e}", exc_info=True)
        raise Exception(f"Failed to get photo sizes: {str(e)}")

    except Exception as e:
        logger.error(f"Error getting photo sizes for {photo_id}: {e}", exc_info=True)
        raise


def download_photo(photo_url: str, timeout: int = 30) -> bytes:
    """
    Download image bytes from a Flickr photo URL.

    Args:
        photo_url: Full URL to the image (e.g., from photo['url_o'] or photo['url_l'])
        timeout: Request timeout in seconds

    Returns:
        Image bytes

    Raises:
        Exception: If download fails or times out

    Example:
        >>> photo_url = photo['url_o'] or photo['url_l'] or photo['url_m']
        >>> image_bytes = download_photo(photo_url)
        >>> print(f"Downloaded {len(image_bytes)} bytes")
    """
    try:
        logger.debug(f"Downloading image from: {photo_url}")

        response = requests.get(photo_url, stream=True, timeout=timeout)
        response.raise_for_status()

        # Read image bytes
        image_bytes = response.content

        logger.debug(f"Downloaded {len(image_bytes)} bytes")
        return image_bytes

    except requests.Timeout:
        logger.error(f"Download timed out after {timeout}s: {photo_url}")
        raise Exception(f"Download timed out after {timeout}s")

    except requests.RequestException as e:
        logger.error(f"Failed to download photo: {e}", exc_info=True)
        raise Exception(f"Failed to download image: {str(e)}")

    except Exception as e:
        logger.error(f"Error downloading photo: {e}", exc_info=True)
        raise


def batch_download_photos(
    photo_data_list: List[Dict],
    max_workers: int = 3
) -> List[Dict]:
    """
    Download multiple photos concurrently using ThreadPoolExecutor.

    Downloads images in parallel with configurable concurrency. Returns results
    with both successful downloads and failures for proper error handling.

    Args:
        photo_data_list: List of photo dicts from search_photos(), each containing
                         'id', 'url_o'/'url_l'/'url_m', and other metadata
        max_workers: Number of concurrent download threads

    Returns:
        List of dicts, one per photo, containing:
            - 'photo_id': Flickr photo ID
            - 'success': True if download succeeded, False otherwise
            - 'image_bytes': Image bytes (if success=True)
            - 'error': Error message (if success=False)
            - 'metadata': Original photo metadata from Flickr

    Example:
        >>> results = search_photos("coffee shop", per_page=10)
        >>> downloads = batch_download_photos(results['photos'], max_workers=5)
        >>> successful = [d for d in downloads if d['success']]
        >>> print(f"Downloaded {len(successful)}/{len(downloads)} images")
    """
    try:
        logger.info(f"Batch downloading {len(photo_data_list)} photos with {max_workers} workers")

        download_results = []

        def download_single_photo(photo: Dict) -> Dict:
            """Download a single photo and return result dict."""
            photo_id = photo.get('id')

            # Get best available URL (original > large > medium)
            url = photo.get('url_o') or photo.get('url_l') or photo.get('url_m')

            if not url:
                return {
                    'photo_id': photo_id,
                    'success': False,
                    'error': 'No URL available',
                    'metadata': photo
                }

            try:
                image_bytes = download_photo(url)
                return {
                    'photo_id': photo_id,
                    'success': True,
                    'image_bytes': image_bytes,
                    'metadata': photo
                }
            except Exception as e:
                return {
                    'photo_id': photo_id,
                    'success': False,
                    'error': str(e),
                    'metadata': photo
                }

        # Execute downloads concurrently
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all download tasks
            futures = {executor.submit(download_single_photo, photo): photo for photo in photo_data_list}

            # Collect results as they complete
            for future in as_completed(futures):
                try:
                    result = future.result()
                    download_results.append(result)

                    # Log progress
                    if len(download_results) % 10 == 0:
                        successful = sum(1 for r in download_results if r['success'])
                        logger.info(f"Progress: {len(download_results)}/{len(photo_data_list)} "
                                  f"({successful} successful)")

                except Exception as e:
                    logger.error(f"Download task failed: {e}", exc_info=True)
                    download_results.append({
                        'photo_id': None,
                        'success': False,
                        'error': str(e),
                        'metadata': {}
                    })

        # Final summary
        successful = sum(1 for r in download_results if r['success'])
        failed = len(download_results) - successful
        logger.info(f"Batch download complete: {successful} successful, {failed} failed")

        return download_results

    except Exception as e:
        logger.error(f"Error in batch download: {e}", exc_info=True)
        raise Exception(f"Batch download failed: {str(e)}")
