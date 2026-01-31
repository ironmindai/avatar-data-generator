"""
OpenAI Image Generation Service
Handles avatar image generation using OpenAI's gpt-image-1.5 model.

This module provides two main image generation functions:
1. generate_base_image: Text-to-image generation from bio
2. generate_images_from_base: Image-to-image generation creating 4-image grid
"""

import os
import base64
import httpx
import logging
from io import BytesIO
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_API_BASE = "https://api.openai.com/v1"
IMAGE_MODEL = "gpt-image-1.5"
IMAGE_GENERATION_TIMEOUT = 600  # 10 minutes timeout


async def generate_base_image(
    bio_facebook: str,
    gender: str,
    randomize_face: bool = False,
    randomize_face_gender_lock: bool = False
) -> Optional[bytes]:
    """
    Generate base avatar image from bio using text-to-image or image-to-image generation.

    Creates a selfie-style image with amateur aesthetic based on the person's
    Facebook bio and gender. Optionally uses a random face from S3 as reference.

    Args:
        bio_facebook: Facebook bio text describing the person
        gender: Gender of the person (for prompt) - 'm' or 'f'
        randomize_face: If True, use random face from S3 with img2img. If False, use txt2img.
        randomize_face_gender_lock: If True and randomize_face=True, select face matching gender

    Returns:
        bytes: Generated image as bytes, or None if generation fails

    Raises:
        Exception: If API call fails or returns invalid response
    """
    try:
        # Convert gender shorthand to full word
        gender_full = 'male' if gender.lower() == 'm' else 'female'

        # Construct the base prompt
        base_prompt = (
            f"generate an image of how this person would look like in a selfie. "
            f"the image should be not well-produced, amateur digital camera aesthetic, "
            f"low resolution. Person: {bio_facebook}. {gender_full}."
        )

        # Check if face randomization is enabled
        if randomize_face:
            logger.info("=" * 80)
            logger.info("FACE RANDOMIZATION ENABLED")
            logger.info(f"Gender Lock: {randomize_face_gender_lock}")
            logger.info("=" * 80)

            # Import S3 faces service
            from services.s3_faces import get_random_face_for_generation

            # Get random face image
            try:
                face_data = await get_random_face_for_generation(
                    gender=gender,
                    gender_lock=randomize_face_gender_lock
                )

                if not face_data:
                    logger.warning("No face images available in S3. Falling back to text-to-image.")
                    randomize_face = False  # Fall back to txt2img
                else:
                    s3_key, public_url, face_image_bytes = face_data
                    logger.info(f"Using random face as reference: {s3_key}")
                    logger.info(f"Face image URL: {public_url}")

            except Exception as e:
                logger.error(f"Failed to get random face: {e}")
                logger.warning("Falling back to text-to-image generation")
                randomize_face = False  # Fall back to txt2img

        # Generate image based on mode
        if randomize_face and face_image_bytes:
            # MODE: Image-to-Image (img2img) with random face reference
            prompt = (
                f"{base_prompt} "
                f"Attached is an image just to draw inspiration from regarding facial anatomy "
                f"and features, not ethnicity or gender."
            )

            logger.info(f"Generating base image for gender '{gender}' using img2img")
            logger.info("=" * 80)
            logger.info("BASE IMAGE GENERATION PROMPT (Image-to-Image with Face Reference):")
            logger.info(f"{prompt}")
            logger.info("=" * 80)

            # Prepare multipart form data for /images/edits endpoint
            image_file = BytesIO(face_image_bytes)
            files = [
                ('image[]', ('reference_face.png', image_file, 'image/png'))
            ]

            data = {
                'prompt': prompt,
                'model': IMAGE_MODEL,
                'n': 1,
                'size': 'auto'
            }

            headers = {
                'Authorization': f'Bearer {OPENAI_API_KEY}'
            }

            # Make async HTTP request to OpenAI img2img endpoint
            async with httpx.AsyncClient(timeout=IMAGE_GENERATION_TIMEOUT) as client:
                response = await client.post(
                    f"{OPENAI_API_BASE}/images/edits",
                    files=files,
                    data=data,
                    headers=headers
                )

                # Check for errors
                response.raise_for_status()
                result = response.json()

                # Extract base64 image data
                if 'data' in result and len(result['data']) > 0:
                    if 'b64_json' in result['data'][0]:
                        base64_image = result['data'][0]['b64_json']
                        image_bytes = base64.b64decode(base64_image)

                        logger.info(f"Successfully generated base image with face reference ({len(image_bytes)} bytes)")
                        return image_bytes
                    else:
                        logger.error("Response data missing 'b64_json' field")
                        raise Exception("Invalid response format: missing b64_json")
                else:
                    logger.error("Response missing 'data' field or data is empty")
                    raise Exception("Invalid response format: missing data")

        else:
            # MODE: Text-to-Image (txt2img) - Original behavior
            prompt = base_prompt

            logger.info(f"Generating base image for gender '{gender}' using txt2img")
            logger.info("=" * 80)
            logger.info("BASE IMAGE GENERATION PROMPT (Text-to-Image):")
            logger.info(f"{prompt}")
            logger.info("=" * 80)

            # Prepare request payload
            payload = {
                "model": IMAGE_MODEL,
                "prompt": prompt,
                "size": "auto",
                "n": 1
            }

            # Prepare headers
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }

            # Make async HTTP request to OpenAI
            async with httpx.AsyncClient(timeout=IMAGE_GENERATION_TIMEOUT) as client:
                response = await client.post(
                    f"{OPENAI_API_BASE}/images/generations",
                    json=payload,
                    headers=headers
                )

                # Check for errors
                response.raise_for_status()
                result = response.json()

                # Extract base64 image data
                if 'data' in result and len(result['data']) > 0:
                    if 'b64_json' in result['data'][0]:
                        base64_image = result['data'][0]['b64_json']
                        image_bytes = base64.b64decode(base64_image)

                        logger.info(f"Successfully generated base image ({len(image_bytes)} bytes)")
                        return image_bytes
                    else:
                        logger.error("Response data missing 'b64_json' field")
                        raise Exception("Invalid response format: missing b64_json")
                else:
                    logger.error("Response missing 'data' field or data is empty")
                    raise Exception("Invalid response format: missing data")

    except httpx.HTTPStatusError as e:
        error_detail = {}
        try:
            error_detail = e.response.json()
        except Exception:
            error_detail = {'text': e.response.text}

        logger.error(f"OpenAI API HTTP error: {e.response.status_code} - {error_detail}")
        raise Exception(f"OpenAI API error: {error_detail}")

    except httpx.TimeoutException:
        logger.error(f"Request timed out after {IMAGE_GENERATION_TIMEOUT}s")
        raise Exception(f"Image generation timed out after {IMAGE_GENERATION_TIMEOUT}s")

    except Exception as e:
        logger.error(f"Error generating base image: {str(e)}", exc_info=True)
        raise Exception(f"Base image generation failed: {str(e)}")


async def generate_images_from_base(
    base_image_bytes: bytes,
    flowise_prompt: str
) -> Optional[bytes]:
    """
    Generate 4-image grid from base image using image-to-image generation.

    Uses OpenAI's /v1/images/edits endpoint to create variations of the base
    image according to the Flowise-generated prompt. Returns a 4-image grid.

    IMPORTANT: This function uses direct HTTP POST (not the SDK) because the
    OpenAI Python SDK does not properly support the image[] field notation
    required for sending the base image.

    Args:
        base_image_bytes: Base image as bytes (from generate_base_image)
        flowise_prompt: Prompt from Flowise workflow describing desired variations

    Returns:
        bytes: Generated 4-image grid as bytes, or None if generation fails

    Raises:
        Exception: If API call fails or returns invalid response
    """
    try:
        logger.info("Generating images from base image")
        logger.info("=" * 80)
        logger.info("FLOWISE IMAGE PROMPT (Image-to-Image for 4-grid):")
        logger.info(f"{flowise_prompt}")
        logger.info("=" * 80)
        logger.info(f"Base image size: {len(base_image_bytes)} bytes")

        # Prepare multipart form data
        # CRITICAL: Use 'image[]' field notation for the image
        # CRITICAL: Wrap bytes in BytesIO to create a file-like object
        # This ensures httpx properly streams the image data like a file handle
        image_file = BytesIO(base_image_bytes)
        files = [
            ('image[]', ('base_image.png', image_file, 'image/png'))
        ]

        # Prepare form data
        data = {
            'prompt': flowise_prompt,
            'model': IMAGE_MODEL,
            'n': 1,
            'size': 'auto'
        }

        # Prepare headers
        headers = {
            'Authorization': f'Bearer {OPENAI_API_KEY}'
        }

        # Make direct HTTP request using httpx
        async with httpx.AsyncClient(timeout=IMAGE_GENERATION_TIMEOUT) as client:
            http_response = await client.post(
                f'{OPENAI_API_BASE}/images/edits',
                files=files,
                data=data,
                headers=headers
            )

            # Check for errors
            http_response.raise_for_status()
            result = http_response.json()

            # Extract base64 image
            if 'data' in result and len(result['data']) > 0:
                if 'b64_json' in result['data'][0]:
                    base64_image = result['data'][0]['b64_json']
                    image_bytes = base64.b64decode(base64_image)

                    logger.info(f"Successfully generated 4-image grid ({len(image_bytes)} bytes)")
                    return image_bytes
                else:
                    logger.error("Response data missing 'b64_json' field")
                    raise Exception("Invalid response format: missing b64_json")
            else:
                logger.error("Response missing 'data' field or data is empty")
                raise Exception("Invalid response format: missing data")

    except httpx.HTTPStatusError as e:
        error_detail = {}
        try:
            error_detail = e.response.json()
        except Exception:
            error_detail = {'text': e.response.text}

        logger.error(f"OpenAI API HTTP error: {e.response.status_code} - {error_detail}")

        # Check for content policy violations
        error_msg = str(error_detail)
        if 'content_policy_violation' in error_msg.lower():
            logger.error("Content policy violation detected")
            raise Exception(f"Content policy violation: {error_detail}")

        raise Exception(f"OpenAI API error: {error_detail}")

    except httpx.TimeoutException:
        logger.error(f"Request timed out after {IMAGE_GENERATION_TIMEOUT}s")
        raise Exception(f"Image generation timed out after {IMAGE_GENERATION_TIMEOUT}s")

    except Exception as e:
        logger.error(f"Error generating images from base: {str(e)}", exc_info=True)
        raise Exception(f"Image-to-image generation failed: {str(e)}")


# Utility function for testing/debugging
async def test_generation():
    """
    Test function to verify image generation works.
    This can be used for debugging or integration testing.
    """
    test_bio = "Software engineer who loves hiking, photography, and coffee. Living in Seattle."
    test_gender = "male"

    logger.info("Testing base image generation...")
    base_image = await generate_base_image(test_bio, test_gender)

    if base_image:
        logger.info("Base image generation successful!")

        test_prompt = "Create 4 variations of this person in different poses and lighting"
        logger.info("Testing image-to-image generation...")
        grid_image = await generate_images_from_base(base_image, test_prompt)

        if grid_image:
            logger.info("Image-to-image generation successful!")
            return True

    return False
