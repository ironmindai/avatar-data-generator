"""
Avatar Image Generation Service
Handles avatar image generation using OpenRouter Nano Banana 2 (Gemini 3.1 Flash Image Preview)
and OpenAI DALL-E as fallback.

This module provides two main image generation functions:
1. generate_base_image: Image-to-image with Nano Banana 2 (primary) or text-to-image with OpenAI (fallback)
2. generate_images_from_base: Image-to-image generation creating 4-image grid
"""

import os
import base64
import httpx
import logging
import asyncio
from io import BytesIO
from typing import Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Flagged images log file path
FLAGGED_IMAGES_LOG = '/home/niro/galacticos/avatar-data-generator/flagged-images.log'

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_API_BASE = "https://api.openai.com/v1"
IMAGE_MODEL = "gpt-image-1.5"
IMAGE_GENERATION_TIMEOUT = 600  # 10 minutes timeout

# Image generation prompt configuration
BASE_PROMPT_APPEND = os.getenv('BASE_PROMPT_APPEND', '').strip()

# Two-stage pipeline configuration
USE_TWO_STAGE_PIPELINE = os.getenv('USE_TWO_STAGE_PIPELINE', 'True').lower() in ('true', '1', 'yes')
SAVE_INTERMEDIATE_IMAGES = os.getenv('SAVE_INTERMEDIATE_IMAGES', 'False').lower() in ('true', '1', 'yes')


def log_flagged_image(image_url: str, reason: str, request_id: Optional[str] = None):
    """
    Log a flagged image URL to the flagged images log file.

    Args:
        image_url: The S3 public URL of the flagged image
        reason: The reason for flagging (e.g., 'moderation_blocked')
        request_id: Optional OpenAI request ID for tracking
    """
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        request_id_str = f" - Request ID: {request_id}" if request_id else ""
        log_entry = f"[{timestamp}] FLAGGED: {image_url} - Reason: {reason}{request_id_str}\n"

        with open(FLAGGED_IMAGES_LOG, 'a') as f:
            f.write(log_entry)

        logger.warning(f"Logged flagged image: {image_url}")

    except Exception as e:
        logger.error(f"Failed to log flagged image: {e}")


def is_moderation_blocked_error(error_detail: dict) -> bool:
    """
    Check if an error response indicates a moderation block.

    Args:
        error_detail: Error response dictionary from OpenAI API

    Returns:
        True if error is a moderation block, False otherwise
    """
    try:
        # Check for 'code' field
        if 'code' in error_detail and error_detail['code'] == 'moderation_blocked':
            return True

        # Check for error dict with code
        if 'error' in error_detail:
            error_obj = error_detail['error']
            if isinstance(error_obj, dict) and error_obj.get('code') == 'moderation_blocked':
                return True

        # Check message for moderation keywords
        message = str(error_detail.get('message', ''))
        if 'moderation_blocked' in message or 'safety_violations' in message:
            return True

        return False

    except Exception as e:
        logger.debug(f"Error checking moderation status: {e}")
        return False


async def generate_base_image(
    bio_facebook: str,
    gender: str,
    randomize_face: bool = False,
    randomize_face_gender_lock: bool = False,
    ethnicity: Optional[str] = None,
    age: Optional[int] = None
) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Generate base avatar image using OpenRouter Nano Banana 2 or text-to-image generation.

    Creates a selfie-style image based on gender, age, and ethnicity.
    Optionally uses a random face from S3 as reference with a simple, effective prompt.

    **Image-to-Image Mode** (if randomize_face=True):
        S3 Random Face → OpenRouter Nano Banana 2 (Gemini 3.1 Flash) → Base Avatar
        Simple prompt: "based on this face, create a {gender} version of a {age} year old, {ethnicity} ethnicity"

    **Text-to-Image Mode** (if randomize_face=False):
        OpenAI DALL-E 3 text-to-image → Base Avatar

    Args:
        bio_facebook: Facebook bio text describing the person (unused in img2img mode)
        gender: Gender of the person - 'm' or 'f' (converted to 'male'/'female')
        randomize_face: If True, use random face from S3 with Nano Banana 2. If False, use txt2img.
        randomize_face_gender_lock: If True and randomize_face=True, select face matching gender
        ethnicity: Ethnicity of the person (e.g., 'Swedish', 'Asian', 'Israeli')
        age: Age of the person (e.g., 23)

    Returns:
        Tuple of (image_bytes, selected_size) or (None, None) if generation fails
        - image_bytes: Generated image as bytes
        - selected_size: Image size string (e.g., "1024x1024", "1024x1536", "1536x1024")

    Raises:
        Exception: If API call fails or returns invalid response
    """
    try:
        import random

        # Convert gender shorthand to full word
        gender_full = 'male' if gender.lower() == 'm' else 'female'

        # Add gender-specific diversity hints to combat model bias
        # Males need extra diversity prompts as training data has less variety
        diversity_hint = ""
        if gender.lower() == 'm':
            import random
            male_diversity = [
                "unique facial features",
                "distinct face shape",
                "individual facial characteristics",
                "varied facial structure",
                "distinctive appearance"
            ]
            diversity_hint = f" {random.choice(male_diversity)}."

        # Randomize base image quality (NO camera/phone mentions to avoid showing devices in frame)
        BASE_QUALITY_STYLES = [
            "Low quality amateur photo. Bad lighting, not professional.",
            "Candid unposed selfie.",
            "Authentic unfiltered social media photo from 2014-2016. Compressed JPEG artifacts.",
            "Deliberately bad photo quality, opposite of Instagram aesthetic. No filters, no editing.",
            "Quick snapshot taken without care or composition. Poor framing, amateur lighting.",
            "Real person, real moment, heavily compressed image. JPEG compression artifacts visible."
        ]

        quality_prefix = random.choice(BASE_QUALITY_STYLES)

        # Randomize image aspect ratio for variety
        ASPECT_RATIOS = ['1024x1024', '1024x1536', '1536x1024']  # square, portrait, landscape
        selected_size = random.choice(ASPECT_RATIOS)
        logger.info(f"Selected aspect ratio: {selected_size}")

        # Construct the base prompt with randomized quality
        # Use "POV selfie" to naturally exclude phone/camera from frame
        base_prompt = (
            f"{quality_prefix} "
            f"POV selfie. "
            f"not well-produced, amateur aesthetic, low resolution. "
            f"Person: {bio_facebook}. {gender_full}.{diversity_hint} "
            f"Close-up portrait showing face and upper body."
        )

        # Add ethnicity if available
        if ethnicity:
            base_prompt += f" Ethnicity: {ethnicity}."

        # Add age if available
        if age:
            base_prompt += f" Age: {age}."

        # Append custom text if configured
        if BASE_PROMPT_APPEND:
            base_prompt = f"{base_prompt} {BASE_PROMPT_APPEND}"

        logger.info(f"Base image quality style: {quality_prefix[:50]}...")

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
            # NEW SIMPLE APPROACH: Use OpenRouter Nano Banana 2 (Gemini 3.1 Flash Image Preview)
            # This is the same model we already use successfully for scene generation
            logger.info("=" * 80)
            logger.info("USING NANO BANANA 2 FOR BASE IMAGE GENERATION")
            logger.info("Model: google/gemini-3.1-flash-image-preview (OpenRouter)")
            logger.info("=" * 80)

            # Import OpenRouter scene service (which has Nano Banana 2)
            from services.openrouter_scene_service import OPENROUTER_API_KEY, OPENROUTER_API_URL

            # Build simple, effective prompt
            # Convert gender m/f to male/female for better results
            gender_word = 'male' if gender.lower() == 'm' else 'female'

            # Simple prompt that works incredibly well with ANY seed image
            simple_prompt = f"based on this face, create a {gender_word} version of a {age} year old, {ethnicity} ethnicity"

            logger.info(f"Gender: {gender_word}")
            logger.info(f"Age: {age}")
            logger.info(f"Ethnicity: {ethnicity}")
            logger.info(f"Reference face: {public_url}")
            logger.info(f"Simple prompt: {simple_prompt}")
            logger.info("=" * 80)

            try:
                # Download reference face and convert to base64
                download_timeout = httpx.Timeout(60.0, connect=30.0)
                async with httpx.AsyncClient(timeout=download_timeout) as client:
                    logger.info("Downloading reference face for base64 encoding...")
                    face_response = await client.get(public_url)
                    if face_response.status_code != 200:
                        raise Exception(f"Failed to download reference face: {face_response.status_code}")
                    face_base64 = base64.b64encode(face_response.content).decode('utf-8')
                    logger.info(f"✓ Downloaded and encoded reference face ({len(face_response.content)} bytes)")

                # Prepare request headers
                headers = {
                    'Authorization': f'Bearer {OPENROUTER_API_KEY}',
                    'Content-Type': 'application/json',
                    'HTTP-Referer': 'https://avatar-data-generator.dev.iron-mind.ai',
                    'X-Title': 'Avatar Data Generator - Base Image'
                }

                # Prepare request payload with single image reference
                payload = {
                    'model': 'google/gemini-3.1-flash-image-preview',
                    'messages': [{
                        'role': 'user',
                        'content': [
                            {
                                'type': 'text',
                                'text': simple_prompt
                            },
                            {
                                'type': 'image_url',
                                'image_url': {
                                    'url': f'data:image/png;base64,{face_base64}'
                                }
                            }
                        ]
                    }],
                    'modalities': ['image'],
                    'temperature': 0.7
                }

                # Call OpenRouter Nano Banana 2
                MAX_RETRIES = 3
                current_attempt = 0

                while current_attempt < MAX_RETRIES:
                    try:
                        current_attempt += 1
                        logger.info(f"Attempt {current_attempt}/{MAX_RETRIES}: Calling OpenRouter Nano Banana 2...")

                        # Make async HTTP request to OpenRouter
                        api_timeout = httpx.Timeout(180.0, connect=30.0)
                        async with httpx.AsyncClient(timeout=api_timeout) as client:
                            response = await client.post(
                                OPENROUTER_API_URL,
                                headers=headers,
                                json=payload
                            )

                            # Check for HTTP errors
                            if response.status_code != 200:
                                error_detail = response.json() if response.text else {'error': 'Unknown error'}
                                logger.error(f"OpenRouter API HTTP error on attempt {current_attempt}: {response.status_code} - {error_detail}")

                                if current_attempt < MAX_RETRIES:
                                    logger.info(f"Retrying in 3 seconds...")
                                    await asyncio.sleep(3)
                                    continue
                                else:
                                    raise Exception(f"OpenRouter API error: {response.status_code} - {error_detail}")

                            # Parse response
                            result = response.json()

                            # Extract image from response
                            if 'choices' not in result or len(result['choices']) == 0:
                                raise Exception("No choices in OpenRouter response")

                            message = result['choices'][0].get('message', {})
                            images = message.get('images', [])

                            if not images or len(images) == 0:
                                raise Exception("No images in OpenRouter response")

                            # Get first image
                            image_data = images[0]
                            image_url = image_data.get('image_url', {}).get('url', '')

                            if not image_url:
                                raise Exception("No image URL in OpenRouter response")

                            # Parse base64 data (format: "data:image/png;base64,{base64_string}")
                            if not image_url.startswith('data:image/'):
                                raise Exception(f"Unexpected image URL format: {image_url[:100]}")

                            # Extract base64 data
                            base64_prefix = 'base64,'
                            base64_start = image_url.find(base64_prefix)
                            if base64_start == -1:
                                raise Exception("No base64 data found in image URL")

                            base64_data = image_url[base64_start + len(base64_prefix):]

                            # Decode base64 to bytes
                            image_bytes = base64.b64decode(base64_data)

                            logger.info(f"Successfully generated base image with Nano Banana 2")
                            logger.info(f"Image size: {len(image_bytes)} bytes")
                            return image_bytes, selected_size

                    except httpx.TimeoutException:
                        logger.error(f"OpenRouter API timeout on attempt {current_attempt}")
                        if current_attempt < MAX_RETRIES:
                            logger.info(f"Retrying in 3 seconds...")
                            await asyncio.sleep(3)
                            continue
                        else:
                            raise Exception("OpenRouter API timeout after all retries")

                    except Exception as e:
                        logger.error(f"Error on attempt {current_attempt}: {str(e)}")
                        if current_attempt < MAX_RETRIES:
                            logger.info(f"Retrying in 3 seconds...")
                            await asyncio.sleep(3)
                            continue
                        else:
                            raise

            except Exception as e:
                logger.error(f"Nano Banana 2 base image generation failed: {str(e)}")
                raise

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
                "size": selected_size,  # Use randomized aspect ratio
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
                        return image_bytes, selected_size
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

        # Try OpenRouter as fallback if configured
        if os.getenv('USE_OPENROUTER', 'False').lower() in ('true', '1', 'yes'):
            openrouter_key = os.getenv('OPENROUTER_API_KEY', '')
            if openrouter_key:
                logger.warning("OpenAI failed, attempting fallback to OpenRouter GPT-5 Image")

                try:
                    from services.openrouter_image_service import generate_image_openrouter

                    logger.info("Using OpenRouter as fallback for base image generation")
                    full_prompt = base_prompt if 'base_prompt' in locals() else prompt
                    image_bytes = await generate_image_openrouter(
                        prompt=full_prompt,
                        size=selected_size
                    )

                    if image_bytes:
                        logger.info(f"✓ Successfully generated base image with OpenRouter ({len(image_bytes)} bytes)")
                        return (image_bytes, selected_size)
                    else:
                        logger.error("OpenRouter returned no image")

                except Exception as openrouter_error:
                    logger.error(f"OpenRouter fallback also failed: {str(openrouter_error)}")
                    # Fall through to raise original OpenAI error
            else:
                logger.warning("USE_OPENROUTER=True but OPENROUTER_API_KEY not configured")

        # If we get here, all methods failed - raise the original error
        raise Exception(f"OpenAI API error: {error_detail}")

    except httpx.TimeoutException:
        logger.error(f"Request timed out after {IMAGE_GENERATION_TIMEOUT}s")
        raise Exception(f"Image generation timed out after {IMAGE_GENERATION_TIMEOUT}s")

    except Exception as e:
        logger.error(f"Error generating base image: {str(e)}", exc_info=True)

        # Try OpenRouter as fallback if configured (only for non-timeout errors)
        if os.getenv('USE_OPENROUTER', 'False').lower() in ('true', '1', 'yes'):
            openrouter_key = os.getenv('OPENROUTER_API_KEY', '')
            if openrouter_key and 'timed out' not in str(e).lower():
                logger.warning("OpenAI failed, attempting fallback to OpenRouter GPT-5 Image")

                try:
                    from services.openrouter_image_service import generate_image_openrouter

                    logger.info("Using OpenRouter as fallback for base image generation")
                    full_prompt = base_prompt if 'base_prompt' in locals() else prompt
                    image_bytes = await generate_image_openrouter(
                        prompt=full_prompt,
                        size=selected_size
                    )

                    if image_bytes:
                        logger.info(f"✓ Successfully generated base image with OpenRouter ({len(image_bytes)} bytes)")
                        return (image_bytes, selected_size)
                    else:
                        logger.error("OpenRouter returned no image")

                except Exception as openrouter_error:
                    logger.error(f"OpenRouter fallback also failed: {str(openrouter_error)}")
                    # Fall through to raise original error
            else:
                if not openrouter_key:
                    logger.warning("USE_OPENROUTER=True but OPENROUTER_API_KEY not configured")

        raise Exception(f"Base image generation failed: {str(e)}")


async def generate_images_from_base(
    base_image_bytes: bytes,
    flowise_prompt: str
) -> Optional[bytes]:
    """
    DEPRECATED: This function is no longer used in the production workflow.
    Replaced by SeeDream individual image generation (seedream_service.py).

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

    Deprecated:
        Use seedream_service.generate_image_with_reference() instead for
        individual image generation with better facial consistency.
    """
    try:
        # Append custom text if configured
        if BASE_PROMPT_APPEND:
            flowise_prompt = f"{flowise_prompt} {BASE_PROMPT_APPEND}"

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


async def _generate_openai_from_base(
    base_image_bytes: bytes,
    bio_facebook: str,
    gender: str,
    ethnicity: Optional[str],
    age: Optional[int],
    quality_prefix: str,
    diversity_hint: str,
    selected_size: str
) -> Optional[bytes]:
    """
    Helper function for Stage 2: OpenAI/DALL-E generation with detailed prompts.

    Uses the intermediate face from RunPod Stage 1 and applies detailed bio,
    ethnicity control, and amateur aesthetic.

    Args:
        base_image_bytes: Intermediate face from RunPod Stage 1
        bio_facebook: Facebook bio text
        gender: 'm' or 'f'
        ethnicity: Ethnicity string
        age: Age integer
        quality_prefix: Pre-selected quality style prefix
        diversity_hint: Pre-generated diversity hint
        selected_size: Image size (e.g., '1024x1024')

    Returns:
        Final avatar image bytes or None
    """
    try:
        # Convert gender shorthand to full word
        gender_full = 'male' if gender.lower() == 'm' else 'female'

        # Build detailed prompt for OpenAI (Stage 2)
        # OpenAI excels at detailed instruction-following and ethnicity control
        prompt = (
            f"{quality_prefix} "
            f"POV selfie. "
            f"not well-produced, amateur aesthetic, low resolution. "
            f"Person: {bio_facebook}. {gender_full}.{diversity_hint} "
            f"Close-up portrait showing face and upper body."
        )

        # Add STRONG ethnicity control (OpenAI's strength)
        if ethnicity:
            prompt += f" STRONG ETHNIC ADHERENCE REQUIRED: {ethnicity} person with authentic {ethnicity} facial features and skin tone."

        # Add age if available
        if age:
            prompt += f" Age: {age}."

        # Append custom text if configured
        if BASE_PROMPT_APPEND:
            prompt = f"{prompt} {BASE_PROMPT_APPEND}"

        logger.info("OpenAI Stage 2 prompt (with full bio + ethnicity control):")
        logger.info(f"{prompt}")

        # Prepare multipart form data for /images/edits endpoint
        image_file = BytesIO(base_image_bytes)
        files = [
            ('image[]', ('runpod_intermediate.png', image_file, 'image/png'))
        ]

        data = {
            'prompt': prompt,
            'model': IMAGE_MODEL,
            'n': 1,
            'size': selected_size,
            'input_fidelity': 'low'  # Low fidelity = creative freedom to apply ethnicity from prompt
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

                    logger.info(f"OpenAI Stage 2 successful ({len(image_bytes)} bytes)")
                    logger.info("=" * 80)
                    return image_bytes
                else:
                    logger.error("OpenAI response missing 'b64_json' field")
                    return None
            else:
                logger.error("OpenAI response missing 'data' field or data is empty")
                return None

    except httpx.HTTPStatusError as e:
        error_detail = {}
        try:
            error_detail = e.response.json()
        except Exception:
            error_detail = {'text': e.response.text}

        logger.error(f"OpenAI Stage 2 HTTP error: {e.response.status_code} - {error_detail}")

        # Try OpenRouter as fallback if configured
        if os.getenv('USE_OPENROUTER', 'False').lower() in ('true', '1', 'yes'):
            openrouter_key = os.getenv('OPENROUTER_API_KEY', '')
            if openrouter_key:
                logger.warning("OpenAI failed in Stage 2, attempting fallback to OpenRouter GPT-5 Image")

                try:
                    from services.openrouter_image_service import generate_image_openrouter

                    logger.info("Using OpenRouter as fallback for Stage 2 generation")
                    image_bytes = await generate_image_openrouter(
                        prompt=prompt,
                        size=selected_size
                    )

                    if image_bytes:
                        logger.info(f"✓ Successfully generated Stage 2 image with OpenRouter ({len(image_bytes)} bytes)")
                        return image_bytes
                    else:
                        logger.error("OpenRouter returned no image")

                except Exception as openrouter_error:
                    logger.error(f"OpenRouter fallback also failed: {str(openrouter_error)}")
            else:
                logger.warning("USE_OPENROUTER=True but OPENROUTER_API_KEY not configured")

        return None

    except Exception as e:
        logger.error(f"Error in OpenAI Stage 2 generation: {str(e)}", exc_info=True)

        # Try OpenRouter as fallback if configured
        if os.getenv('USE_OPENROUTER', 'False').lower() in ('true', '1', 'yes'):
            openrouter_key = os.getenv('OPENROUTER_API_KEY', '')
            if openrouter_key:
                logger.warning("OpenAI failed in Stage 2, attempting fallback to OpenRouter GPT-5 Image")

                try:
                    from services.openrouter_image_service import generate_image_openrouter

                    logger.info("Using OpenRouter as fallback for Stage 2 generation")
                    image_bytes = await generate_image_openrouter(
                        prompt=prompt,
                        size=selected_size
                    )

                    if image_bytes:
                        logger.info(f"✓ Successfully generated Stage 2 image with OpenRouter ({len(image_bytes)} bytes)")
                        return image_bytes
                    else:
                        logger.error("OpenRouter returned no image")

                except Exception as openrouter_error:
                    logger.error(f"OpenRouter fallback also failed: {str(openrouter_error)}")
            else:
                logger.warning("USE_OPENROUTER=True but OPENROUTER_API_KEY not configured")

        return None


# Utility function for testing/debugging
async def test_generation():
    """
    Test function to verify image generation works.
    This can be used for debugging or integration testing.
    """
    test_bio = "Software engineer who loves hiking, photography, and coffee. Living in Seattle."
    test_gender = "male"

    logger.info("Testing base image generation...")
    base_image, selected_size = await generate_base_image(test_bio, test_gender)

    if base_image:
        logger.info(f"Base image generation successful! Size: {selected_size}")

        test_prompt = "Create 4 variations of this person in different poses and lighting"
        logger.info("Testing image-to-image generation...")
        grid_image = await generate_images_from_base(base_image, test_prompt)

        if grid_image:
            logger.info("Image-to-image generation successful!")
            return True

    return False
