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

from PIL import Image, ImageChops, PngImagePlugin
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
S3_PUBLIC_URL_BASE = os.getenv('S3_PUBLIC_URL_BASE', 'https://minio.electric-marinade.com')


def split_and_trim_image(
    image_bytes: bytes,
    num_rows: int = 2,
    num_cols: int = 2
) -> List[bytes]:
    """
    DEPRECATED: This function is no longer used in the production workflow.
    Replaced by SeeDream individual image generation (no grid splitting needed).

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

    Deprecated:
        Images are now generated individually via SeeDream, eliminating the need
        for grid splitting. This function remains for backwards compatibility.
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
        # output_dir: Save splits to our temp directory instead of current directory
        split_image(temp_input_path, num_rows, num_cols, should_square=False, should_cleanup=False, output_dir=temp_dir)

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


def embed_metadata_in_png(image_bytes: bytes, metadata: dict) -> bytes:
    """
    Embed metadata into PNG image file as text chunks.

    This allows metadata to survive downloads - it's embedded in the image file itself,
    not just stored in S3 object metadata.

    Args:
        image_bytes: Original image bytes (PNG or JPEG)
        metadata: Dictionary of metadata key-value pairs to embed

    Returns:
        bytes: New PNG image with embedded metadata
    """
    try:
        # Load image from bytes
        img = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if necessary (remove alpha channel for JPEG compatibility)
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')

        # Create PNG info object to store metadata as text chunks
        png_info = PngImagePlugin.PngInfo()

        for key, value in metadata.items():
            # Add each metadata pair as a PNG text chunk
            png_info.add_text(key, str(value))
            logger.debug(f"Embedded metadata: {key} = {value[:100]}...")

        # Save to bytes with metadata
        output_buffer = io.BytesIO()
        img.save(output_buffer, format='PNG', pnginfo=png_info)
        return output_buffer.getvalue()

    except Exception as e:
        logger.warning(f"Failed to embed metadata in PNG: {e}")
        # Return original bytes if embedding fails
        return image_bytes


def upload_to_s3(
    image_bytes: bytes,
    object_key: str,
    bucket_name: str = None,
    content_type: str = 'image/png',
    metadata: dict = None
) -> Tuple[str, str]:
    """
    Upload an image to S3-compatible storage (MinIO) with optional metadata.

    Uploads image bytes to the configured S3 bucket and returns the
    object key and a public URL for accessing the image.

    Args:
        image_bytes: Image data as bytes
        object_key: S3 object key (path/filename in bucket), e.g., 'avatars/123/image_0.png'
        bucket_name: S3 bucket name (defaults to S3_BUCKET_NAME from .env)
        content_type: MIME type of the image (default: 'image/png')
        metadata: Optional dict of metadata key-value pairs to attach to the S3 object
                  (e.g., {'prompt': 'scene description', 'degradation': 'quality style'})

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

        # Embed metadata into image file if provided
        image_to_upload = image_bytes
        if metadata:
            logger.debug(f"Embedding metadata into image file: {list(metadata.keys())}")
            image_to_upload = embed_metadata_in_png(image_bytes, metadata)

        logger.info(f"Uploading image to S3: {bucket}/{object_key} ({len(image_to_upload)} bytes)")

        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            endpoint_url=S3_ENDPOINT,
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
            config=Config(signature_version='s3v4'),
            region_name=S3_REGION
        )

        # Prepare put_object parameters
        put_params = {
            'Bucket': bucket,
            'Key': object_key,
            'Body': image_to_upload,
            'ContentType': content_type
        }

        # Note: We no longer attach metadata to S3 headers because:
        # 1. S3 metadata has ASCII-only limitation (fails on accented characters)
        # 2. Metadata is already embedded in the PNG file itself (survives downloads)
        # 3. PNG text chunks support full UTF-8 and are more portable

        # Upload the image
        s3_client.put_object(**put_params)

        # Construct public URL
        # Format: {S3_PUBLIC_URL_BASE}/bucket/object_key
        # Note: Use public endpoint, not internal S3_ENDPOINT (which is localhost)
        public_url = f"{S3_PUBLIC_URL_BASE}/{bucket}/{object_key}"

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


def generate_presigned_url(
    object_key: str,
    bucket_name: str = None,
    expiration: int = 3600
) -> str:
    """
    Generate a presigned URL for an S3 object using the PUBLIC endpoint.

    This allows temporary public access to a private S3 object without
    making the bucket public. Useful for passing image URLs to external APIs
    like SeeDream that need to download the image.

    IMPORTANT: Uses S3_PUBLIC_URL_BASE instead of S3_ENDPOINT to ensure
    the URL is accessible from external services (not localhost).

    Args:
        object_key: S3 object key (path/filename in bucket)
        bucket_name: S3 bucket name (defaults to S3_BUCKET_NAME from .env)
        expiration: URL expiration time in seconds (default: 3600 = 1 hour)

    Returns:
        str: Presigned URL that provides temporary access to the object

    Raises:
        Exception: If S3 credentials are missing or URL generation fails
    """
    try:
        # Use provided bucket name or default from environment
        bucket = bucket_name or S3_BUCKET_NAME

        # Validate configuration
        if not all([S3_PUBLIC_URL_BASE, S3_ACCESS_KEY, S3_SECRET_KEY, bucket]):
            logger.error("S3 configuration incomplete")
            raise Exception(
                "S3 configuration missing. Check S3_PUBLIC_URL_BASE, S3_ACCESS_KEY, "
                "S3_SECRET_KEY, and S3_BUCKET_NAME in .env"
            )

        logger.debug(f"Generating presigned URL for {bucket}/{object_key} (expiry: {expiration}s)")

        # Initialize S3 client with PUBLIC endpoint (not localhost)
        # This ensures the presigned URL uses the public domain that external services can access
        s3_client = boto3.client(
            's3',
            endpoint_url=S3_PUBLIC_URL_BASE,  # Use public URL, not localhost
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
            config=Config(signature_version='s3v4'),
            region_name=S3_REGION
        )

        # Generate presigned URL
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket,
                'Key': object_key
            },
            ExpiresIn=expiration
        )

        logger.debug(f"Presigned URL generated: {presigned_url[:100]}...")
        logger.info(f"Presigned URL uses public endpoint: {S3_PUBLIC_URL_BASE}")
        return presigned_url

    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', str(e))

        logger.error(f"S3 presigned URL generation failed - {error_code}: {error_message}")
        raise Exception(f"S3 presigned URL error ({error_code}): {error_message}")

    except Exception as e:
        logger.error(f"Error generating presigned URL: {str(e)}", exc_info=True)
        raise Exception(f"Presigned URL generation failed: {str(e)}")


def delete_from_s3(
    object_key: str,
    bucket_name: str = None
) -> bool:
    """
    Delete an object from S3-compatible storage (MinIO).

    Args:
        object_key: S3 object key (path/filename in bucket) to delete
        bucket_name: S3 bucket name (defaults to S3_BUCKET_NAME from .env)

    Returns:
        bool: True if deletion was successful

    Raises:
        Exception: If S3 deletion fails or credentials are missing
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

        logger.info(f"Deleting object from S3: {bucket}/{object_key}")

        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            endpoint_url=S3_ENDPOINT,
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
            config=Config(signature_version='s3v4'),
            region_name=S3_REGION
        )

        # Delete the object
        s3_client.delete_object(
            Bucket=bucket,
            Key=object_key
        )

        logger.info(f"Successfully deleted from S3: {bucket}/{object_key}")
        return True

    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', str(e))

        logger.error(f"S3 deletion failed - {error_code}: {error_message}")

        # NoSuchKey is not an error - object already doesn't exist
        if error_code == 'NoSuchKey':
            logger.warning(f"Object {object_key} does not exist, treating as successful deletion")
            return True

        if error_code == 'NoSuchBucket':
            raise Exception(f"S3 bucket '{bucket}' does not exist")
        elif error_code == 'AccessDenied':
            raise Exception(f"S3 access denied. Check credentials and bucket permissions")
        else:
            raise Exception(f"S3 deletion error ({error_code}): {error_message}")

    except Exception as e:
        logger.error(f"Error deleting from S3: {str(e)}", exc_info=True)
        raise Exception(f"S3 deletion failed: {str(e)}")


def delete_s3_url(
    s3_url: str
) -> bool:
    """
    Delete an S3 object given its public URL.

    Extracts the bucket name and object key from the public S3 URL
    and deletes the object.

    Args:
        s3_url: Full S3 public URL (e.g., 'https://s3-api.dev.iron-mind.ai/avatars/image.png')

    Returns:
        bool: True if deletion was successful

    Raises:
        Exception: If URL parsing fails or S3 deletion fails
    """
    try:
        # Extract bucket and object key from URL
        # URL format: {S3_PUBLIC_URL_BASE}/{bucket}/{object_key}
        # Example: https://s3-api.dev.iron-mind.ai/avatars/task_123/image_0.png

        # Remove the base URL
        if not s3_url.startswith(S3_PUBLIC_URL_BASE):
            raise Exception(f"URL does not start with expected base: {S3_PUBLIC_URL_BASE}")

        # Get the path after the base URL
        path = s3_url[len(S3_PUBLIC_URL_BASE):].lstrip('/')

        # Split into bucket and object key
        parts = path.split('/', 1)
        if len(parts) != 2:
            raise Exception(f"Could not parse bucket and object key from URL: {s3_url}")

        bucket_name = parts[0]
        object_key = parts[1]

        logger.debug(f"Parsed S3 URL - bucket: {bucket_name}, key: {object_key}")

        # Delete the object
        return delete_from_s3(object_key, bucket_name)

    except Exception as e:
        logger.error(f"Error deleting S3 URL {s3_url}: {str(e)}", exc_info=True)
        raise Exception(f"S3 URL deletion failed: {str(e)}")


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
