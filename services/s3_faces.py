"""
S3 Faces Service
Handles random face selection from MinIO S3 bucket OR image datasets for base image generation.

This module provides functions to:
1. List available face images from S3 bucket
2. Select random face images based on gender from S3 faces bucket
3. Select random face images from image datasets (alternative source)
4. Download face images for use in img2img generation

Configuration:
- BASE_IMAGE_FACE_SOURCE: 's3_faces' (default) or 'image_datasets'
- BASE_IMAGE_DATASET_IDS: Comma-separated dataset IDs (when using image_datasets source)
"""

import os
import random
import logging
import httpx
from typing import Optional, List, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# S3 Configuration
S3_ENDPOINT = os.getenv('S3_ENDPOINT', 'http://127.0.0.1:9000')
S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
S3_SECRET_KEY = os.getenv('S3_SECRET_KEY')
S3_REGION = os.getenv('S3_REGION', 'us-east-1')
FACES_BUCKET = 'faces'

# Public URL format for MinIO
# Assuming public access is configured, URLs follow: endpoint/bucket/key
S3_PUBLIC_URL_BASE = os.getenv('S3_PUBLIC_URL_BASE', 'https://s3-api.dev.iron-mind.ai')


def get_s3_client():
    """
    Get boto3 S3 client configured for MinIO.

    Returns:
        boto3 S3 client configured with MinIO credentials

    Raises:
        Exception: If boto3 is not installed or client creation fails
    """
    try:
        import boto3
        from botocore.client import Config

        client = boto3.client(
            's3',
            endpoint_url=S3_ENDPOINT,
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
            region_name=S3_REGION,
            config=Config(signature_version='s3v4')
        )
        return client
    except ImportError:
        raise Exception("boto3 library is required for S3 operations. Please install it: pip install boto3")
    except Exception as e:
        logger.error(f"Failed to create S3 client: {e}")
        raise


def list_face_images(gender: Optional[str] = None) -> List[str]:
    """
    List all face images from S3 bucket, optionally filtered by gender.

    Args:
        gender: Optional gender filter ('m' or 'f'). If None, lists all images.

    Returns:
        List of S3 object keys (e.g., 'male/face1.jpg', 'female/face2.png')

    Raises:
        Exception: If S3 listing fails
    """
    try:
        s3_client = get_s3_client()

        # Determine prefix based on gender
        if gender:
            gender_full = 'male' if gender.lower() == 'm' else 'female'
            prefix = f"{gender_full}/"
        else:
            prefix = ""

        logger.info(f"Listing face images from s3://{FACES_BUCKET}/{prefix}")

        # List objects in bucket
        response = s3_client.list_objects_v2(
            Bucket=FACES_BUCKET,
            Prefix=prefix
        )

        if 'Contents' not in response:
            logger.warning(f"No objects found in s3://{FACES_BUCKET}/{prefix}")
            return []

        # Filter for image files only (jpg, jpeg, png)
        image_extensions = ('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG')
        face_keys = [
            obj['Key'] for obj in response['Contents']
            if obj['Key'].lower().endswith(image_extensions)
        ]

        logger.info(f"Found {len(face_keys)} face images in s3://{FACES_BUCKET}/{prefix}")
        return face_keys

    except Exception as e:
        logger.error(f"Failed to list face images from S3: {e}", exc_info=True)
        raise Exception(f"S3 listing failed: {str(e)}")


def select_random_face(gender: Optional[str] = None) -> Optional[Tuple[str, str]]:
    """
    Select a random face image from S3 bucket.

    Args:
        gender: Optional gender filter ('m' or 'f'). If None, selects from all images.

    Returns:
        Tuple of (s3_key, public_url) or None if no images found
        Example: ('male/face1.jpg', 'https://s3-api.dev.iron-mind.ai/faces/male/face1.jpg')

    Raises:
        Exception: If S3 operations fail
    """
    try:
        # Get list of available face images
        face_keys = list_face_images(gender)

        if not face_keys:
            gender_str = f"gender '{gender}'" if gender else "any gender"
            logger.warning(f"No face images available for {gender_str}")
            return None

        # Select random image
        selected_key = random.choice(face_keys)

        # Construct public URL
        public_url = f"{S3_PUBLIC_URL_BASE}/{FACES_BUCKET}/{selected_key}"

        logger.info(f"Selected random face: {selected_key}")
        logger.info(f"Public URL: {public_url}")

        return selected_key, public_url

    except Exception as e:
        logger.error(f"Failed to select random face: {e}", exc_info=True)
        raise Exception(f"Random face selection failed: {str(e)}")


async def download_face_image(s3_key: str) -> Optional[bytes]:
    """
    Download a face image from S3 using the public URL.

    Args:
        s3_key: S3 object key (e.g., 'male/face1.jpg')

    Returns:
        Image bytes or None if download fails

    Raises:
        Exception: If download fails
    """
    try:
        # Construct public URL
        public_url = f"{S3_PUBLIC_URL_BASE}/{FACES_BUCKET}/{s3_key}"

        logger.info(f"Downloading face image from: {public_url}")

        # Download using httpx
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(public_url)
            response.raise_for_status()

            image_bytes = response.content
            logger.info(f"Downloaded face image: {len(image_bytes)} bytes")

            return image_bytes

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error downloading face image: {e.response.status_code}")
        raise Exception(f"Failed to download face image: HTTP {e.response.status_code}")
    except Exception as e:
        logger.error(f"Error downloading face image: {e}", exc_info=True)
        raise Exception(f"Face image download failed: {str(e)}")


async def get_random_face_for_generation(
    gender: str,
    gender_lock: bool = True
) -> Optional[Tuple[str, str, bytes]]:
    """
    Get a random face image for use in image generation.

    This is a convenience function that combines selection and download.

    Args:
        gender: Person's gender ('m' or 'f')
        gender_lock: If True, select from matching gender folder. If False, select from any.

    Returns:
        Tuple of (s3_key, public_url, image_bytes) or None if no images available

    Raises:
        Exception: If S3 operations fail
    """
    try:
        # Determine gender filter
        target_gender = gender if gender_lock else None

        if gender_lock:
            logger.info(f"Selecting random face with gender lock: {gender}")
        else:
            logger.info("Selecting random face without gender lock (any gender)")

        # Select random face
        selection = select_random_face(target_gender)

        if not selection:
            return None

        s3_key, public_url = selection

        # Download face image (await since we're async now)
        image_bytes = await download_face_image(s3_key)

        if not image_bytes:
            raise Exception("Downloaded image is empty")

        logger.info(f"Successfully retrieved random face: {s3_key}")
        return s3_key, public_url, image_bytes

    except Exception as e:
        logger.error(f"Failed to get random face for generation: {e}", exc_info=True)
        raise Exception(f"Random face retrieval failed: {str(e)}")


async def get_random_face_from_datasets(
    dataset_ids: List,  # Can be List[int] or List[str] (UUIDs)
    gender: Optional[str] = None,
    gender_lock: bool = False
) -> Optional[Tuple[str, str, bytes]]:
    """
    Get a random face image from specified image datasets for base image generation.

    This is an alternative to S3 faces bucket - uses image datasets instead.
    Useful when you want to use curated datasets as face sources.

    NOTE: Gender filtering is typically NOT used when sourcing from datasets,
    as datasets are usually mixed or untagged by gender. Set gender_lock=False.

    Args:
        dataset_ids: List of dataset IDs (integers) or dataset_ids (UUIDs/strings)
        gender: Optional gender filter ('m' or 'f') - typically ignored
        gender_lock: If True, attempts gender filtering (usually False for datasets)

    Returns:
        Tuple of (dataset_name_id, public_url, image_bytes) or None if no images available

    Raises:
        Exception: If database or download operations fail

    Example:
        >>> face_data = await get_random_face_from_datasets([1, 2, 3])
        >>> if face_data:
        >>>     identifier, url, image_bytes = face_data
    """
    try:
        from models import db, DatasetImage, ImageDataset

        logger.info(f"Selecting random face from image datasets: {dataset_ids}")

        if gender_lock and gender:
            logger.warning(
                f"Gender filtering (gender={gender}, lock={gender_lock}) is typically NOT applicable "
                f"for image datasets (no gender metadata). Ignoring gender filter."
            )

        # Query random image from specified datasets
        # Order by random to get a different image each time
        from sqlalchemy import func

        # Support both integer IDs and UUID dataset_ids
        # Check if dataset_ids are integers or UUIDs
        if dataset_ids and isinstance(dataset_ids[0], str) and len(dataset_ids[0]) > 10:
            # Looks like UUIDs (strings > 10 chars)
            logger.info(f"Detected UUID format for dataset IDs, querying by dataset_id column")
            random_image = db.session.query(
                DatasetImage.id,
                DatasetImage.image_url,
                ImageDataset.name.label('dataset_name')
            ).join(
                ImageDataset, DatasetImage.dataset_id == ImageDataset.id
            ).filter(
                ImageDataset.dataset_id.in_(dataset_ids)  # Use dataset_id (UUID) column
            ).order_by(
                func.random()
            ).first()
        else:
            # Integer IDs
            logger.info(f"Detected integer format for dataset IDs, querying by id column")
            random_image = db.session.query(
                DatasetImage.id,
                DatasetImage.image_url,
                ImageDataset.name.label('dataset_name')
            ).join(
                ImageDataset, DatasetImage.dataset_id == ImageDataset.id
            ).filter(
                ImageDataset.id.in_(dataset_ids)  # Use id (integer) column
            ).order_by(
                func.random()
            ).first()

        if not random_image:
            logger.warning(f"No images found in datasets: {dataset_ids}")
            return None

        image_id = random_image.id
        image_url = random_image.image_url
        dataset_name = random_image.dataset_name

        logger.info(f"Selected image {image_id} from dataset '{dataset_name}'")
        logger.info(f"Image URL: {image_url}")

        # Download image
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(image_url)
            response.raise_for_status()

            image_bytes = response.content
            logger.info(f"Downloaded dataset face image: {len(image_bytes)} bytes")

        # Return identifier (dataset_name_imageID), URL, and bytes
        identifier = f"{dataset_name}_{image_id}"
        return identifier, image_url, image_bytes

    except Exception as e:
        logger.error(f"Failed to get random face from datasets: {e}", exc_info=True)
        raise Exception(f"Dataset face retrieval failed: {str(e)}")


async def get_random_face_unified(
    gender: str,
    gender_lock: bool = True
) -> Optional[Tuple[str, str, bytes]]:
    """
    Unified function to get random face from either S3 faces bucket OR image datasets.

    This function checks the configuration and routes to the appropriate source:
    - BASE_IMAGE_FACE_SOURCE='s3_faces' → Use S3 faces bucket (default)
    - BASE_IMAGE_FACE_SOURCE='image_datasets' → Use image datasets

    Configuration via environment or Config table:
    - BASE_IMAGE_FACE_SOURCE: Source type ('s3_faces' or 'image_datasets')
    - BASE_IMAGE_DATASET_IDS: Comma-separated dataset IDs (for 'image_datasets' mode)

    Args:
        gender: Person's gender ('m' or 'f')
        gender_lock: If True, filter by gender (only works for s3_faces)

    Returns:
        Tuple of (identifier, public_url, image_bytes) or None if no images available

    Raises:
        Exception: If configuration is invalid or retrieval fails

    Example:
        >>> face_data = await get_random_face_unified('m', gender_lock=True)
        >>> if face_data:
        >>>     identifier, url, image_bytes = face_data
    """
    try:
        # Check configuration source
        face_source = os.getenv('BASE_IMAGE_FACE_SOURCE', 's3_faces')

        if face_source == 's3_faces':
            # Use S3 faces bucket (original behavior)
            logger.info(f"Using S3 faces bucket as base image source")
            return await get_random_face_for_generation(gender, gender_lock)

        elif face_source == 'image_datasets':
            # Use image datasets
            logger.info(f"Using image datasets as base image source")

            # Get dataset IDs from environment or Config
            dataset_ids_str = os.getenv('BASE_IMAGE_DATASET_IDS', '')

            # Try Config table if env not set
            if not dataset_ids_str:
                try:
                    from models import IntConfig
                    config_value = IntConfig.get_value('base_image_dataset_ids', None)
                    if config_value:
                        dataset_ids_str = str(config_value)
                except Exception:
                    pass

            if not dataset_ids_str:
                raise ValueError(
                    "BASE_IMAGE_FACE_SOURCE is 'image_datasets' but BASE_IMAGE_DATASET_IDS is not configured. "
                    "Set BASE_IMAGE_DATASET_IDS to comma-separated dataset IDs (e.g., '1,2,3')"
                )

            # Parse dataset IDs - support both integers and UUIDs
            try:
                raw_ids = [x.strip() for x in dataset_ids_str.split(',') if x.strip()]

                # Try to parse as integers first
                try:
                    dataset_ids = [int(x) for x in raw_ids]
                    logger.info(f"Parsed dataset IDs as integers: {dataset_ids}")
                except ValueError:
                    # Not integers, treat as UUIDs (strings)
                    dataset_ids = raw_ids
                    logger.info(f"Parsed dataset IDs as UUIDs: {dataset_ids}")

            except Exception as e:
                raise ValueError(f"Invalid BASE_IMAGE_DATASET_IDS format: '{dataset_ids_str}'. Error: {e}")

            if not dataset_ids:
                raise ValueError("BASE_IMAGE_DATASET_IDS is empty. At least one dataset ID is required.")

            logger.info(f"Using dataset identifiers for base images: {dataset_ids}")

            # Gender filtering note
            if gender_lock:
                logger.info(
                    f"Note: Gender lock is enabled (gender={gender}), but image datasets "
                    f"typically don't have gender metadata. Gender filtering will be skipped."
                )

            return await get_random_face_from_datasets(dataset_ids, gender, gender_lock)

        else:
            raise ValueError(
                f"Invalid BASE_IMAGE_FACE_SOURCE: '{face_source}'. "
                f"Must be 's3_faces' or 'image_datasets'."
            )

    except Exception as e:
        logger.error(f"Failed to get random face (unified): {e}", exc_info=True)
        raise
