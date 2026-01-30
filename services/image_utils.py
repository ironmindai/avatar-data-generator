"""
Image Processing and S3 Upload Service
Handles image splitting, trimming whitespace, and uploading to S3 storage.

This module provides functionality to:
1. Split a 4-image grid into individual images
2. Trim whitespace from each split image
3. Upload images to S3-compatible storage (MinIO)
"""

import os
import io
import tempfile
import logging
from typing import List, Tuple
from pathlib import Path
from dotenv import load_dotenv

from PIL import Image, ImageChops
from split_image import split_image
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# S3 Configuration
S3_ENDPOINT = os.getenv('S3_ENDPOINT')
S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
S3_SECRET_KEY = os.getenv('S3_SECRET_KEY')
S3_REGION = os.getenv('S3_REGION', 'us-east-1')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')


def split_and_trim_image(
    image_bytes: bytes,
    num_rows: int = 2,
    num_cols: int = 2
) -> List[bytes]:
    """
    Split a grid image into individual images and trim whitespace from each.

    Takes a 4-image grid (2x2) and splits it into 4 separate images,
    then trims any whitespace/padding from each individual image.

    Args:
        image_bytes: The grid image as bytes (e.g., from OpenAI API)
        num_rows: Number of rows in the grid (default: 2)
        num_cols: Number of columns in the grid (default: 2)

    Returns:
        List[bytes]: List of trimmed image bytes, one per grid cell.
                     For a 2x2 grid, returns 4 image bytes objects.

    Raises:
        Exception: If image splitting or trimming fails
    """
    temp_dir = None
    try:
        logger.info(f"Splitting {num_rows}x{num_cols} grid image ({len(image_bytes)} bytes)")

        # Create temporary directory for processing
        temp_dir = tempfile.mkdtemp(prefix='avatar_split_')
        temp_input_path = os.path.join(temp_dir, 'input_grid.png')

        # Save input bytes to temporary file
        with open(temp_input_path, 'wb') as f:
            f.write(image_bytes)

        # Split the image using split-image library
        # This creates files: input_grid_0.png, input_grid_1.png, etc.
        # should_square=False: Don't force squares, keep original aspect ratio
        split_image(temp_input_path, num_rows, num_cols, should_square=False, should_cleanup=False)

        # Calculate total number of splits
        num_splits = num_rows * num_cols

        # Process each split image: trim whitespace and collect bytes
        trimmed_images = []
        for i in range(num_splits):
            split_filename = f"input_grid_{i}.png"
            split_path = os.path.join(temp_dir, split_filename)

            if not os.path.exists(split_path):
                logger.error(f"Expected split file not found: {split_path}")
                raise Exception(f"Split file {split_filename} not created")

            # Trim whitespace from this split
            trimmed_bytes = _trim_whitespace_from_file(split_path)
            trimmed_images.append(trimmed_bytes)

            logger.debug(f"Processed split {i}: {len(trimmed_bytes)} bytes after trimming")

        logger.info(f"Successfully split and trimmed {num_splits} images")
        return trimmed_images

    except Exception as e:
        logger.error(f"Error splitting and trimming image: {str(e)}", exc_info=True)
        raise Exception(f"Image splitting failed: {str(e)}")

    finally:
        # Clean up temporary files
        if temp_dir and os.path.exists(temp_dir):
            try:
                import shutil
                shutil.rmtree(temp_dir)
                logger.debug(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory {temp_dir}: {str(e)}")


def _trim_whitespace_from_file(image_path: str) -> bytes:
    """
    Trim whitespace/padding from an image file and return as bytes.

    Uses PIL ImageChops.invert to detect content boundaries and crop
    to the actual content, removing any white padding/borders.

    Args:
        image_path: Path to the image file to trim

    Returns:
        bytes: Trimmed image as PNG bytes

    Raises:
        Exception: If image loading or trimming fails
    """
    try:
        # Open the image
        img = Image.open(image_path)

        # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
        img_rgb = img.convert('RGB')

        # Invert the image to detect content boundaries
        # This makes white areas black and content areas visible
        inverted = ImageChops.invert(img_rgb)

        # Get the bounding box of non-black (i.e., non-white in original) areas
        bbox = inverted.getbbox()

        if bbox:
            # Crop to the content area
            trimmed = img.crop(bbox)
        else:
            # If no bounding box found, return original image
            logger.warning(f"No content detected for trimming in {image_path}, using original")
            trimmed = img

        # Convert to bytes
        output_buffer = io.BytesIO()
        trimmed.save(output_buffer, format='PNG')
        trimmed_bytes = output_buffer.getvalue()

        return trimmed_bytes

    except Exception as e:
        logger.error(f"Error trimming whitespace from {image_path}: {str(e)}", exc_info=True)
        raise Exception(f"Whitespace trimming failed: {str(e)}")


def upload_to_s3(
    image_bytes: bytes,
    object_key: str,
    bucket_name: str = None,
    content_type: str = 'image/png'
) -> Tuple[str, str]:
    """
    Upload an image to S3-compatible storage (MinIO).

    Uploads image bytes to the configured S3 bucket and returns the
    object key and a public URL for accessing the image.

    Args:
        image_bytes: Image data as bytes
        object_key: S3 object key (path/filename in bucket), e.g., 'avatars/123/image_0.png'
        bucket_name: S3 bucket name (defaults to S3_BUCKET_NAME from .env)
        content_type: MIME type of the image (default: 'image/png')

    Returns:
        Tuple[str, str]: (object_key, public_url)
                         - object_key: The S3 object key used for storage
                         - public_url: Full URL to access the image

    Raises:
        Exception: If S3 upload fails or credentials are missing
    """
    try:
        # Use provided bucket name or default from environment
        bucket = bucket_name or S3_BUCKET_NAME

        # Validate configuration
        if not all([S3_ENDPOINT, S3_ACCESS_KEY, S3_SECRET_KEY, bucket]):
            logger.error("S3 configuration incomplete")
            raise Exception(
                "S3 configuration missing. Check S3_ENDPOINT, S3_ACCESS_KEY, "
                "S3_SECRET_KEY, and S3_BUCKET_NAME in .env"
            )

        logger.info(f"Uploading image to S3: {bucket}/{object_key} ({len(image_bytes)} bytes)")

        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            endpoint_url=S3_ENDPOINT,
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
            config=Config(signature_version='s3v4'),
            region_name=S3_REGION
        )

        # Upload the image
        s3_client.put_object(
            Bucket=bucket,
            Key=object_key,
            Body=image_bytes,
            ContentType=content_type
        )

        # Construct public URL
        # Format: https://s3-api.dev.iron-mind.ai/bucket/object_key
        # Note: Use public endpoint, not internal S3_ENDPOINT (which is localhost)
        public_url = f"https://s3-api.dev.iron-mind.ai/{bucket}/{object_key}"

        logger.info(f"Successfully uploaded to S3: {public_url}")
        return object_key, public_url

    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', str(e))

        logger.error(f"S3 upload failed - {error_code}: {error_message}")

        # Check for common errors
        if error_code == 'NoSuchBucket':
            raise Exception(f"S3 bucket '{bucket}' does not exist")
        elif error_code == 'AccessDenied':
            raise Exception(f"S3 access denied. Check credentials and bucket permissions")
        else:
            raise Exception(f"S3 upload error ({error_code}): {error_message}")

    except Exception as e:
        logger.error(f"Error uploading to S3: {str(e)}", exc_info=True)
        raise Exception(f"S3 upload failed: {str(e)}")


def upload_images_batch(
    images: List[bytes],
    base_object_key: str,
    bucket_name: str = None
) -> List[Tuple[str, str]]:
    """
    Upload multiple images to S3 in a batch.

    Convenience function to upload a list of images (e.g., the 4 splits
    from split_and_trim_image) with numbered suffixes.

    Args:
        images: List of image bytes to upload
        base_object_key: Base S3 path, e.g., 'avatars/task_123/image'
                         Will append '_0.png', '_1.png', etc.
        bucket_name: S3 bucket name (defaults to S3_BUCKET_NAME from .env)

    Returns:
        List[Tuple[str, str]]: List of (object_key, public_url) tuples,
                                one for each uploaded image

    Raises:
        Exception: If any upload fails
    """
    results = []

    try:
        logger.info(f"Batch uploading {len(images)} images to S3")

        for i, image_bytes in enumerate(images):
            # Construct object key with index suffix
            object_key = f"{base_object_key}_{i}.png"

            # Upload individual image
            key, url = upload_to_s3(image_bytes, object_key, bucket_name)
            results.append((key, url))

        logger.info(f"Successfully uploaded {len(results)} images in batch")
        return results

    except Exception as e:
        logger.error(f"Error in batch upload: {str(e)}", exc_info=True)
        raise Exception(f"Batch upload failed after {len(results)} successful uploads: {str(e)}")


# Utility function for testing/debugging
async def test_image_processing():
    """
    Test function to verify image splitting and S3 upload.
    This can be used for debugging or integration testing.
    """
    try:
        # This would typically use a real 4-image grid from OpenAI
        logger.info("Testing image processing and S3 upload...")

        # For testing, we'd need actual image bytes
        # In production, this comes from generate_images_from_base()

        # Example workflow:
        # 1. Get 4-image grid from OpenAI
        # grid_bytes = await generate_images_from_base(...)

        # 2. Split and trim
        # split_images = split_and_trim_image(grid_bytes)

        # 3. Upload to S3
        # results = upload_images_batch(split_images, 'avatars/test/image')

        logger.info("Test would be run with actual image data")
        return True

    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        return False
