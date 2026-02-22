"""
S3 Style Images Service
Handles random style image selection from MinIO S3 bucket for dual-reference generation.

This module provides functions to:
1. List available style reference images from S3 bucket
2. Select random style images for quality/aesthetic reference
3. Generate presigned URLs for use with SeeDream API
"""

import os
import random
import logging
from typing import Optional, List
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
STYLE_BUCKET = 'style-references'

# Public URL format for MinIO
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


def list_style_images() -> List[str]:
    """
    List all style reference images from S3 bucket.

    Returns:
        List of S3 object keys (e.g., 'style-001.png', 'style-002.png')

    Raises:
        Exception: If S3 listing fails
    """
    try:
        s3_client = get_s3_client()

        logger.debug(f"Listing style images from s3://{STYLE_BUCKET}/")

        # List objects in bucket
        response = s3_client.list_objects_v2(
            Bucket=STYLE_BUCKET
        )

        if 'Contents' not in response:
            logger.warning(f"No objects found in s3://{STYLE_BUCKET}/")
            return []

        # Extract object keys
        style_keys = [obj['Key'] for obj in response['Contents']]

        logger.info(f"Found {len(style_keys)} style images in S3")
        return style_keys

    except Exception as e:
        logger.error(f"Failed to list style images from S3: {e}")
        raise


def get_random_style_image() -> Optional[str]:
    """
    Get a random style reference image URL from S3.

    This function lists all available style images and randomly selects one,
    then generates a presigned URL for use with SeeDream API.

    Returns:
        str: Presigned URL of a random style image, or None if no images available

    Raises:
        Exception: If S3 operations fail
    """
    try:
        # List all style images
        style_keys = list_style_images()

        if not style_keys:
            logger.warning("No style images available in S3 bucket")
            return None

        # Select random style image
        selected_key = random.choice(style_keys)
        logger.info(f"Selected random style image: {selected_key}")

        # Generate presigned URL (valid for 1 hour)
        try:
            from services.image_utils import generate_presigned_url
        except ImportError:
            from image_utils import generate_presigned_url

        presigned_url = generate_presigned_url(
            object_key=selected_key,
            bucket_name=STYLE_BUCKET,
            expiration=3600
        )

        logger.info(f"Generated presigned URL for style image: {presigned_url[:80]}...")
        return presigned_url

    except Exception as e:
        logger.error(f"Failed to get random style image: {e}")
        raise


# Utility function for testing
def test_random_style_selection():
    """
    Test function to verify style image selection works.
    """
    try:
        logger.info("Testing random style image selection...")

        # Get random style image
        style_url = get_random_style_image()

        if style_url:
            logger.info(f"✅ Random style image URL: {style_url}")
            return True
        else:
            logger.warning("⚠️ No style images available")
            return False

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


if __name__ == '__main__':
    # Configure logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run test
    test_random_style_selection()
