"""
SeeDream Image Generation Service
Handles image generation using ByteDance's SeeDream 4.5 API with base image reference.

This service replaces OpenAI's image generation for the 4 additional images
(after base image). It uses SeeDream's txt2img endpoint with the base image
as a reference to maintain facial consistency.
"""

import os
import httpx
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# SeeDream Configuration
SEEDREAM_API_URL = os.getenv('SEEDREAM_API_URL', 'https://ark.ap-southeast.bytepluses.com/api/v3/images/generations')
SEEDREAM_API_KEY = os.getenv('BYTEPLUS_API')  # Using BYTEPLUS_API as specified
SEEDREAM_MODEL = os.getenv('SEEDREAM_MODEL', 'seedream-4-5-251128')
SEEDREAM_IMAGE_SIZE = os.getenv('SEEDREAM_IMAGE_SIZE', '2560x1440')
SEEDREAM_WATERMARK = os.getenv('SEEDREAM_WATERMARK', 'false').lower() == 'true'
SEEDREAM_TIMEOUT = 600  # 10 minutes timeout


async def generate_image_with_reference(
    prompt: str,
    base_image_url: str,
    style_image_url: Optional[str] = None
) -> Optional[bytes]:
    """
    Generate an image using SeeDream 4.5 with single or dual image references.

    This function calls SeeDream's txt2img endpoint with image references:
    - Single-reference mode: Uses only base_image_url for facial consistency
    - Dual-reference mode: Uses base_image_url (person/identity) + style_image_url (quality/aesthetic)

    Args:
        prompt: Text prompt describing the desired image
        base_image_url: Publicly accessible URL of the base image (Image 1 - person/identity)
                       (must be accessible by SeeDream API - use S3 presigned URL)
        style_image_url: Optional URL of style reference image (Image 2 - quality/aesthetic).
                        If provided, uses dual-reference mode. If None, uses single reference.

    Returns:
        bytes: Generated image as bytes, or None if generation fails

    Raises:
        Exception: If API call fails or returns invalid response
    """
    try:
        # Validate configuration
        if not SEEDREAM_API_KEY:
            raise ValueError("BYTEPLUS_API not found in environment variables")

        logger.info(f"Generating image with SeeDream 4.5")
        logger.info("=" * 80)
        logger.info(f"PROMPT: {prompt}")

        # Prepare image reference (single or dual)
        if style_image_url:
            # Dual-reference mode: [Image 1 = person, Image 2 = style]
            image_param = [base_image_url, style_image_url]
            logger.info(f"Using DUAL-REFERENCE mode")
            logger.info(f"  Image 1 (person): {base_image_url}")
            logger.info(f"  Image 2 (style): {style_image_url}")
        else:
            # Single-reference mode (legacy)
            image_param = base_image_url
            logger.info(f"Using SINGLE-REFERENCE mode")
            logger.info(f"  Reference image: {base_image_url}")

        logger.info("=" * 80)

        # Prepare request payload
        # Per KB docs: image field can be string (single) or array (multiple)
        payload = {
            'model': SEEDREAM_MODEL,
            'prompt': prompt,
            'size': SEEDREAM_IMAGE_SIZE,
            'watermark': SEEDREAM_WATERMARK,
            'sequential_image_generation': 'disabled',
            'response_format': 'url',
            'image': image_param  # Can be string or array
        }

        # Prepare headers
        headers = {
            'Authorization': f'Bearer {SEEDREAM_API_KEY}',
            'Content-Type': 'application/json'
        }

        logger.debug(f"Calling SeeDream API: {SEEDREAM_API_URL}")

        # DEBUG: Log the actual payload being sent
        import json
        logger.info(f"SeeDream Payload: {json.dumps(payload, indent=2)}")

        # Make async HTTP request to SeeDream
        async with httpx.AsyncClient(timeout=SEEDREAM_TIMEOUT) as client:
            response = await client.post(
                SEEDREAM_API_URL,
                json=payload,
                headers=headers
            )

            # Check for errors
            response.raise_for_status()
            result = response.json()

            logger.debug(f"SeeDream API response received")

            # Extract image URL from response
            # Per KB docs: response format is { "data": [{"url": "..."}], "created": ..., "id": ... }
            if 'data' not in result or not result['data']:
                logger.error("Response missing 'data' field or data is empty")
                logger.error(f"Full response: {result}")
                raise Exception("Invalid SeeDream response format: missing data")

            image_url = result['data'][0].get('url')
            if not image_url:
                logger.error("Response data missing 'url' field")
                logger.error(f"Full response: {result}")
                raise Exception("Invalid SeeDream response format: missing url")

            logger.info(f"Image generated successfully: {image_url}")

            # Download the generated image from CDN
            logger.debug(f"Downloading image from CDN: {image_url}")
            async with httpx.AsyncClient(timeout=120) as download_client:
                download_response = await download_client.get(image_url)
                download_response.raise_for_status()
                image_bytes = download_response.content

            logger.info(f"Downloaded image: {len(image_bytes)} bytes")
            return image_bytes

    except httpx.HTTPStatusError as e:
        error_detail = {}
        try:
            error_detail = e.response.json()
        except Exception:
            error_detail = {'text': e.response.text}

        logger.error(f"SeeDream API HTTP error: {e.response.status_code} - {error_detail}")
        raise Exception(f"SeeDream API error ({e.response.status_code}): {error_detail}")

    except httpx.TimeoutException:
        logger.error(f"Request timed out after {SEEDREAM_TIMEOUT}s")
        raise Exception(f"SeeDream image generation timed out after {SEEDREAM_TIMEOUT}s")

    except Exception as e:
        logger.error(f"Error generating image with SeeDream: {str(e)}", exc_info=True)
        raise Exception(f"SeeDream image generation failed: {str(e)}")


async def generate_images_batch(
    prompts: list[str],
    base_image_url: str,
    style_image_url: Optional[str] = None
) -> list[bytes]:
    """
    Generate multiple images sequentially using SeeDream with single or dual image references.

    Args:
        prompts: List of text prompts for each image
        base_image_url: Publicly accessible URL of the base image (Image 1 - person/identity)
        style_image_url: Optional URL of style reference image (Image 2 - quality/aesthetic)

    Returns:
        List of generated images as bytes

    Raises:
        Exception: If any generation fails
    """
    try:
        logger.info(f"Generating {len(prompts)} images in batch with SeeDream")

        images = []
        for i, prompt in enumerate(prompts, 1):
            logger.info(f"Generating image {i}/{len(prompts)}...")

            image_bytes = await generate_image_with_reference(
                prompt=prompt,
                base_image_url=base_image_url,
                style_image_url=style_image_url
            )

            images.append(image_bytes)
            logger.info(f"Successfully generated image {i}/{len(prompts)}")

        logger.info(f"Batch generation complete: {len(images)} images")
        return images

    except Exception as e:
        logger.error(f"Error in batch generation: {str(e)}", exc_info=True)
        raise Exception(f"Batch generation failed at image {i}/{len(prompts)}: {str(e)}")


# Utility function for testing/debugging
async def test_generation():
    """
    Test function to verify SeeDream image generation works.
    This can be used for debugging or integration testing.
    """
    try:
        logger.info("Testing SeeDream image generation...")

        # Test prompt
        test_prompt = (
            "Generate an image of a 28 year old female, casual social media quality—"
            "not well-produced, amateur digital camera aesthetic, low resolution. "
            "Create a composition showing: mirror selfie trying on clothes in a dressing room, "
            "grainy smartphone photo, harsh overhead lighting, awkward off-center framing"
        )

        # You would need a real base image URL for testing
        # For now, this is just a placeholder
        test_base_url = "https://example.com/base-image.png"

        logger.info("Note: This test requires a valid base image URL")
        logger.info(f"Test prompt: {test_prompt}")

        # In production, you'd call:
        # image_bytes = await generate_image_with_reference(test_prompt, test_base_url)

        logger.info("Test would be run with actual base image URL")
        return True

    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False
