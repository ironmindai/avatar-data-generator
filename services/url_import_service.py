"""
URL Import Service

This module provides functionality for importing images from external URLs into
the Image Datasets feature. It handles URL validation, image downloading,
and batch import with concurrency.

Key Features:
- URL validation with Content-Type checking
- Batch import with concurrent downloads
- S3 upload integration
- Image hash computation for duplicate detection
- Database integration for tracking imported images
"""

import requests
import logging
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from models import db, DatasetImage
from services.image_utils import upload_dataset_image_to_s3, compute_image_hash

# Configure logging
logger = logging.getLogger(__name__)

# Configuration
DEFAULT_TIMEOUT = 30  # seconds
DEFAULT_MAX_WORKERS = 5
MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50 MB max file size


def validate_image_url(url: str) -> Tuple[bool, str]:
    """
    Validate that a URL is accessible and points to an image.

    Performs a HEAD request to check Content-Type header without downloading
    the full image. Falls back to GET if HEAD is not supported.

    Args:
        url: URL to validate

    Returns:
        Tuple of (is_valid: bool, error_message: str)
        - If valid: (True, "")
        - If invalid: (False, "Error description")

    Example:
        >>> is_valid, error = validate_image_url("https://example.com/photo.jpg")
        >>> if not is_valid:
        ...     print(f"Invalid: {error}")
    """
    try:
        logger.debug(f"Validating URL: {url}")

        # Basic URL validation
        if not url:
            return False, "URL is empty"

        if not url.startswith(('http://', 'https://')):
            return False, "URL must start with http:// or https://"

        # Try HEAD request first (faster, doesn't download content)
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)

            # Some servers don't support HEAD, fall back to GET with stream
            if response.status_code == 405:  # Method Not Allowed
                logger.debug(f"HEAD not supported for {url}, trying GET")
                response = requests.get(url, timeout=10, stream=True, allow_redirects=True)
                # Close connection immediately after headers
                response.close()

            response.raise_for_status()

        except requests.HTTPError as e:
            return False, f"HTTP error: {e.response.status_code}"

        except requests.Timeout:
            return False, "Request timed out"

        except requests.RequestException as e:
            return False, f"Request failed: {str(e)}"

        # Check Content-Type header
        content_type = response.headers.get('Content-Type', '').lower()

        if not content_type:
            return False, "No Content-Type header found"

        # Check if it's an image
        if not content_type.startswith('image/'):
            return False, f"Not an image (Content-Type: {content_type})"

        # Check Content-Length if available
        content_length = response.headers.get('Content-Length')
        if content_length:
            size = int(content_length)
            if size > MAX_IMAGE_SIZE:
                return False, f"Image too large: {size / 1024 / 1024:.1f} MB (max {MAX_IMAGE_SIZE / 1024 / 1024} MB)"
            if size == 0:
                return False, "Image is empty (0 bytes)"

        logger.debug(f"URL validated successfully: {url} (Content-Type: {content_type})")
        return True, ""

    except Exception as e:
        logger.error(f"Unexpected error validating URL {url}: {e}", exc_info=True)
        return False, f"Validation error: {str(e)}"


def download_image_from_url(url: str, timeout: int = DEFAULT_TIMEOUT) -> bytes:
    """
    Download image bytes from a URL.

    Validates Content-Type during download and enforces size limits.

    Args:
        url: URL to download from
        timeout: Request timeout in seconds

    Returns:
        Image bytes

    Raises:
        Exception: If download fails, URL is invalid, or image is not valid

    Example:
        >>> image_bytes = download_image_from_url("https://example.com/photo.jpg")
        >>> print(f"Downloaded {len(image_bytes)} bytes")
    """
    try:
        logger.debug(f"Downloading image from: {url}")

        # Make request with streaming to handle large files
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()

        # Validate Content-Type
        content_type = response.headers.get('Content-Type', '').lower()
        if not content_type.startswith('image/'):
            raise Exception(f"URL does not point to an image (Content-Type: {content_type})")

        # Check Content-Length if available
        content_length = response.headers.get('Content-Length')
        if content_length:
            size = int(content_length)
            if size > MAX_IMAGE_SIZE:
                raise Exception(f"Image too large: {size / 1024 / 1024:.1f} MB (max {MAX_IMAGE_SIZE / 1024 / 1024} MB)")

        # Download with size limit enforcement
        image_bytes = b''
        for chunk in response.iter_content(chunk_size=8192):
            image_bytes += chunk

            # Enforce max size during download
            if len(image_bytes) > MAX_IMAGE_SIZE:
                raise Exception(f"Image exceeds maximum size of {MAX_IMAGE_SIZE / 1024 / 1024} MB")

        if not image_bytes:
            raise Exception("Downloaded image is empty")

        logger.debug(f"Downloaded {len(image_bytes)} bytes from {url}")
        return image_bytes

    except requests.Timeout:
        logger.error(f"Download timed out after {timeout}s: {url}")
        raise Exception(f"Download timed out after {timeout}s")

    except requests.HTTPError as e:
        logger.error(f"HTTP error downloading {url}: {e}")
        raise Exception(f"HTTP error {e.response.status_code}: {e.response.reason}")

    except requests.RequestException as e:
        logger.error(f"Request failed for {url}: {e}", exc_info=True)
        raise Exception(f"Download failed: {str(e)}")

    except Exception as e:
        logger.error(f"Error downloading image from {url}: {e}", exc_info=True)
        raise


def batch_import_urls(
    urls: List[str],
    dataset_id: int,
    app=None,
    max_workers: int = DEFAULT_MAX_WORKERS
) -> Dict:
    """
    Import multiple images from URLs concurrently into a dataset.

    Downloads images, uploads them to S3, computes hashes, and inserts
    records into the dataset_images table. Handles failures gracefully
    and returns detailed results.

    Args:
        urls: List of image URLs to import
        dataset_id: Database ID of the ImageDataset to add images to
        app: Flask application instance for context management (optional, uses current_app if not provided)
        max_workers: Number of concurrent download/upload threads

    Returns:
        Dict containing:
            - 'imported': Number of successfully imported images
            - 'failed': Number of failed imports
            - 'failed_urls': List of dicts with 'url' and 'error' for each failure

    Example:
        >>> urls = ["https://example.com/photo1.jpg", "https://example.com/photo2.jpg"]
        >>> result = batch_import_urls(urls, dataset_id=123, max_workers=5)
        >>> print(f"Imported {result['imported']}, Failed {result['failed']}")
    """
    try:
        from flask import current_app as flask_app

        # Use provided app or current Flask app
        if app is None:
            app = flask_app

        logger.info(f"Batch importing {len(urls)} URLs into dataset {dataset_id} with {max_workers} workers")

        imported_count = 0
        failed_count = 0
        failed_urls = []

        def import_single_url(url: str) -> Dict:
            """Import a single URL and return result dict with proper app context."""
            # Always run database operations within app context
            with app.app_context():
                try:
                    # Step 1: Download image directly (no pre-validation for speed)
                    # The download function will validate Content-Type and fail if not an image
                    image_bytes = download_image_from_url(url)

                    # Step 2: Compute image hash (for tracking, not for duplicate checking during import)
                    # Note: We skip duplicate checking during URL import for performance.
                    # Users can filter/remove duplicates later using the UI.
                    image_hash = compute_image_hash(image_bytes)

                    # Step 3: Determine file extension from Content-Type
                    try:
                        response = requests.head(url, timeout=5, allow_redirects=True)
                        content_type = response.headers.get('Content-Type', '').lower()

                        # Map Content-Type to file extension
                        ext_map = {
                            'image/jpeg': 'jpg',
                            'image/jpg': 'jpg',
                            'image/png': 'png',
                            'image/gif': 'gif',
                            'image/webp': 'webp',
                            'image/bmp': 'bmp',
                            'image/tiff': 'tiff',
                        }
                        file_extension = ext_map.get(content_type, 'jpg')  # Default to jpg

                    except Exception:
                        # If we can't determine extension, default to jpg
                        file_extension = 'jpg'
                        logger.debug(f"Could not determine file extension for {url}, using jpg")

                    # Step 5: Upload to S3
                    # Use hash as source_id for URL imports (unique and meaningful)
                    object_key, public_url = upload_dataset_image_to_s3(
                        image_bytes=image_bytes,
                        dataset_id=dataset_id,
                        source_id=image_hash[:16],  # Use first 16 chars of hash
                        file_extension=file_extension
                    )

                    # Step 6: Face detection disabled during import - will be processed by background job
                    # This prevents worker crashes and keeps imports fast and reliable
                    face_count = None

                    # Step 7: Insert into database
                    dataset_image = DatasetImage(
                        dataset_id=dataset_id,
                        image_url=public_url,
                        source_type='url',  # Must match filter buttons in template (data-filter="url")
                        source_id=image_hash,  # Use hash (64 chars) instead of URL to avoid 255 char limit
                        source_metadata={
                            'original_url': url,  # Full URL stored here (no length limit in JSON)
                            'content_type': content_type if 'content_type' in locals() else None,
                            'file_size': len(image_bytes)
                        },
                        image_hash=image_hash,
                        face_count=face_count  # Store face detection result
                    )
                    db.session.add(dataset_image)
                    db.session.commit()

                    logger.debug(f"Successfully imported URL: {url} -> {public_url}")

                    return {
                        'success': True,
                        'url': url,
                        'image_url': public_url
                    }

                except Exception as e:
                    # Rollback any database changes on error
                    try:
                        db.session.rollback()
                    except Exception as rollback_error:
                        logger.warning(f"Error rolling back session: {rollback_error}")

                    logger.error(f"Failed to import URL {url}: {e}", exc_info=True)
                    return {
                        'success': False,
                        'url': url,
                        'error': str(e)
                    }

        # Execute imports concurrently
        # Timeout per URL: 60 seconds (generous for large images)
        TIMEOUT_PER_URL = 60

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all import tasks
            futures = {executor.submit(import_single_url, url): url for url in urls}

            # Collect results as they complete
            for future in as_completed(futures, timeout=TIMEOUT_PER_URL * len(urls)):
                try:
                    # Get result with timeout
                    result = future.result(timeout=TIMEOUT_PER_URL)

                    if result['success']:
                        imported_count += 1
                    else:
                        failed_count += 1
                        failed_urls.append({
                            'url': result['url'],
                            'error': result['error']
                        })

                    # Log progress
                    total_processed = imported_count + failed_count
                    if total_processed % 10 == 0:
                        logger.info(f"Progress: {total_processed}/{len(urls)} "
                                  f"(imported: {imported_count}, failed: {failed_count})")

                except Exception as e:
                    # Handle timeout or other errors
                    failed_count += 1
                    url = futures.get(future, 'unknown')
                    error_msg = str(e)
                    logger.error(f"Import task failed for {url}: {error_msg}", exc_info=True)
                    failed_urls.append({
                        'url': url,
                        'error': error_msg
                    })

        # Final summary
        logger.info(f"Batch import complete: {imported_count} imported, {failed_count} failed")

        return {
            'imported': imported_count,
            'failed': failed_count,
            'failed_urls': failed_urls
        }

    except Exception as e:
        logger.error(f"Error in batch URL import: {e}", exc_info=True)
        raise Exception(f"Batch import failed: {str(e)}")
