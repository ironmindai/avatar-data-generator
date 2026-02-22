"""
RunPod Image Generation Service
Handles Stage 1 base face generation using RunPod ComfyUI endpoint with Flux model.

This service is used in the two-stage avatar generation pipeline:
- Stage 1 (RunPod/Flux): Generate diverse base faces with simple visual prompts
- Stage 2 (OpenAI/DALL-E): Apply detailed bio, ethnicity control, and amateur aesthetic

RunPod uses Flux (CLIP-based model) which excels at visual/aesthetic but NOT
detailed instruction-following. Keep prompts simple and visual.
"""

import os
import asyncio
import httpx
import random
import logging
from typing import Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# RunPod Configuration
RUNPOD_API_KEY = os.getenv('RUNPOD_API_KEY', 'rpa_J35GATUFIYLG7HFV7VZU9V1NMDBYVT6KA6QQJNMSo5wj5l')
RUNPOD_ENDPOINT_ID = os.getenv('RUNPOD_ENDPOINT_ID', '7l3f8add2h9701')
RUNPOD_API_BASE = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}"
RUNPOD_TIMEOUT = int(os.getenv('RUNPOD_TIMEOUT', '2400'))  # 40 minutes default
RUNPOD_POLL_INTERVAL = int(os.getenv('RUNPOD_POLL_INTERVAL', '10'))  # 10 seconds

# Optimized parameters from testing (see docs/runpod-base-image-generation.md)
RUNPOD_DENOISE = float(os.getenv('RUNPOD_DENOISE', '0.47'))
RUNPOD_IP_WEIGHT = float(os.getenv('RUNPOD_IP_WEIGHT', '0.75'))
RUNPOD_GUIDANCE_SCALE = float(os.getenv('RUNPOD_GUIDANCE_SCALE', '7.5'))
RUNPOD_STEPS = int(os.getenv('RUNPOD_STEPS', '30'))

# Ethnicity to visual prompt mapping (simple descriptions for Flux)
ETHNICITY_VISUAL_MAP = {
    'Swedish': 'fair skin, light hair, Northern European',
    'Norwegian': 'fair skin, light hair, Nordic features',
    'Danish': 'fair skin, light hair, Scandinavian',
    'Finnish': 'fair skin, light hair, Nordic',
    'Icelandic': 'fair skin, light hair, Nordic',

    'Spanish': 'olive skin, Mediterranean features',
    'Italian': 'olive complexion, Mediterranean',
    'Greek': 'olive skin, Mediterranean',
    'Portuguese': 'olive skin, Southern European',

    'Israeli': 'olive skin, dark hair, Middle Eastern features',
    'Jewish': 'varied features, Middle Eastern to European',
    'Arab': 'olive to tan skin, Middle Eastern features',
    'Lebanese': 'olive skin, Middle Eastern',
    'Turkish': 'olive skin, Mediterranean to Middle Eastern',

    'Chinese': 'East Asian features, dark hair',
    'Japanese': 'East Asian features, dark hair',
    'Korean': 'East Asian features, dark hair',
    'Vietnamese': 'Southeast Asian features',
    'Thai': 'Southeast Asian features',

    'Indian': 'South Asian features, brown skin',
    'Pakistani': 'South Asian features',
    'Bangladeshi': 'South Asian features',

    'Nigerian': 'African features, dark skin',
    'Kenyan': 'African features, dark skin',
    'Ethiopian': 'African features, varied skin tone',
    'African': 'African features, dark skin',
    'Black': 'African features, dark skin',

    'Mexican': 'Latin features, varied skin tone',
    'Brazilian': 'Latin American features, varied skin',
    'Colombian': 'Latin features',
    'Argentinian': 'European to Latin mixed features',

    'British': 'European features, varied skin',
    'Irish': 'fair to light skin, European',
    'German': 'European features, light to medium skin',
    'French': 'European features',
    'Polish': 'European features, light skin',
    'Russian': 'Eastern European features',

    'White': 'Caucasian features, light to medium skin',
    'Caucasian': 'European features',
    'European': 'European features',

    'Mixed': 'mixed ethnic features',
    'Multiracial': 'diverse ethnic features'
}


def build_simple_visual_prompt(
    gender: str,
    ethnicity: Optional[str] = None,
    age: Optional[int] = None
) -> str:
    """
    Build a simple visual prompt for Flux (CLIP-based model).

    Flux is NOT good at complex instructions, so keep it simple and visual.
    Focus on gender, basic ethnicity descriptors, and "natural portrait".

    Args:
        gender: 'm' or 'f'
        ethnicity: Optional ethnicity (e.g., 'Swedish', 'Spanish', 'Israeli')
        age: Optional age (will be ignored for now - Flux not great with age)

    Returns:
        Simple visual prompt (under 20 words)
    """
    gender_word = 'man' if gender.lower() == 'm' else 'woman'

    # Get simple visual descriptors from ethnicity
    visual_desc = ''
    if ethnicity and ethnicity in ETHNICITY_VISUAL_MAP:
        visual_desc = f", {ETHNICITY_VISUAL_MAP[ethnicity]}"

    # Keep it VERY simple - Flux limitation
    prompt = f"{gender_word}{visual_desc}, natural portrait"

    logger.debug(f"Built simple visual prompt: {prompt}")
    return prompt


def build_negative_prompt(gender: str) -> str:
    """
    Build gender-specific negative prompt.

    Args:
        gender: 'm' or 'f'

    Returns:
        Negative prompt string
    """
    # Base negative prompt (common to both)
    base = (
        "(smile:1.2), (hand:1.3), "
        "nude, body, porn, nudity, sexual, explicit, erotic, semi-nude, "
        "NSFW, underwear, lingerie, adult, erotic pose, beautiful, gorgeous, "
        "handsome, good looking, sexy, pretty, cartoon, cgi, render, "
        "illustration, painting, drawing, bad quality, grainy, low resolution"
    )

    # Gender-specific additions
    if gender.lower() == 'm':
        # For males: avoid female features
        return f"female, {base}"
    else:
        # For females: avoid male features and facial hair
        return f"male, (beard:1.4), (facial hair:1.4), {base}"


async def generate_runpod_base_face(
    reference_face_url: str,
    gender: str,
    ethnicity: Optional[str] = None,
    age: Optional[int] = None,
    save_debug: bool = False
) -> Optional[bytes]:
    """
    Stage 1: Generate base face using RunPod/Flux with simple visual prompts.

    This function uses RunPod's ComfyUI endpoint with Flux model to create
    diverse base faces from reference images. Flux excels at visual/aesthetic
    but NOT detailed instructions, so prompts are kept simple.

    Args:
        reference_face_url: S3 URL to reference face for diversity
        gender: 'm' or 'f'
        ethnicity: Optional ethnicity for simple visual description
        age: Optional age (mostly ignored - Flux not great with age)
        save_debug: If True, log the intermediate image URL for debugging

    Returns:
        bytes: Generated image as bytes, or None if generation fails

    Raises:
        Exception: If API call fails or returns invalid response
    """
    try:
        logger.info("=" * 80)
        logger.info("STAGE 1: RunPod/Flux Base Face Generation")
        logger.info("=" * 80)

        # Build simple visual prompt (Flux limitation)
        prompt = build_simple_visual_prompt(gender, ethnicity, age)
        negative_prompt = build_negative_prompt(gender)

        logger.info(f"Gender: {gender}")
        logger.info(f"Ethnicity: {ethnicity}")
        logger.info(f"Reference face: {reference_face_url}")
        logger.info(f"Simple visual prompt: {prompt}")
        logger.info(f"Denoise: {RUNPOD_DENOISE}, IP Weight: {RUNPOD_IP_WEIGHT}, Guidance: {RUNPOD_GUIDANCE_SCALE}")

        # Build payload
        payload = {
            "input": {
                "generation_type": "face_generator",
                "random_seeds": [random.randint(0, int(1e9)) for _ in range(4)],
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": 1024,
                "height": 1024,
                "face_image": reference_face_url,
                "denoise": RUNPOD_DENOISE,
                "ip_adapter_weight": RUNPOD_IP_WEIGHT,
                "ip_adapter_start": 0.2,
                "ip_adapter_end": 0.6
            }
        }

        # Queue job
        logger.info("Queueing RunPod job...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{RUNPOD_API_BASE}/run",
                json=payload,
                headers={
                    "Authorization": f"Bearer {RUNPOD_API_KEY}",
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            job_data = response.json()
            job_id = job_data.get("id")

            if not job_id:
                logger.error(f"No job ID in response: {job_data}")
                raise Exception("RunPod API error: No job ID returned")

            logger.info(f"Job queued successfully: {job_id}")

        # Poll for completion
        image_url = await _poll_runpod_job(job_id)

        if not image_url:
            logger.error("RunPod job failed or timed out")
            return None

        logger.info(f"RunPod generation successful!")
        logger.info(f"Image URL returned: {image_url}")

        # Validate and fix URL if needed
        if not image_url.startswith(('http://', 'https://')):
            logger.warning(f"URL missing protocol, adding https://: {image_url}")
            image_url = f"https://{image_url}"

        if save_debug:
            logger.info(f"Intermediate image URL (for debugging): {image_url}")

        # Download image bytes
        logger.info("Downloading generated image...")
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(image_url)
            response.raise_for_status()
            image_bytes = response.content

        logger.info(f"Successfully downloaded RunPod image ({len(image_bytes)} bytes)")
        logger.info("=" * 80)

        return image_bytes

    except httpx.HTTPStatusError as e:
        logger.error(f"RunPod API HTTP error: {e.response.status_code} - {e.response.text}")
        raise Exception(f"RunPod API error: {e.response.status_code}")

    except httpx.TimeoutException:
        logger.error(f"RunPod request timed out")
        raise Exception("RunPod request timed out")

    except Exception as e:
        logger.error(f"Error in RunPod base face generation: {str(e)}", exc_info=True)
        raise


async def _poll_runpod_job(
    job_id: str,
    max_attempts: int = None,
    interval_sec: int = None
) -> Optional[str]:
    """
    Poll RunPod job until completion.

    Args:
        job_id: RunPod job ID
        max_attempts: Maximum polling attempts (default: calculated from RUNPOD_TIMEOUT)
        interval_sec: Polling interval in seconds (default: RUNPOD_POLL_INTERVAL)

    Returns:
        Image URL if successful, None otherwise
    """
    if max_attempts is None:
        max_attempts = RUNPOD_TIMEOUT // RUNPOD_POLL_INTERVAL

    if interval_sec is None:
        interval_sec = RUNPOD_POLL_INTERVAL

    logger.info(f"Polling RunPod job (max {max_attempts * interval_sec / 60:.1f} min)...")

    start_time = datetime.now()
    status_url = f"{RUNPOD_API_BASE}/status/{job_id}"

    async with httpx.AsyncClient() as client:
        for attempt in range(1, max_attempts + 1):
            try:
                response = await client.get(
                    status_url,
                    headers={"Authorization": f"Bearer {RUNPOD_API_KEY}"},
                    timeout=15.0
                )
                response.raise_for_status()
                data = response.json()
                status = data.get("status")

                # Log progress every minute
                if attempt % (60 // interval_sec) == 0:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    logger.info(f"[{elapsed:.0f}s] Status: {status} (attempt {attempt}/{max_attempts})")

                if status == "COMPLETED":
                    output = data.get("output")

                    # Handle string output (direct URL)
                    if isinstance(output, str):
                        image_url = output
                        elapsed = (datetime.now() - start_time).total_seconds()
                        logger.info(f"RunPod job completed in {elapsed:.1f}s")
                        logger.info(f"Image URL: {image_url}")
                        return image_url

                    # Handle list output (face_generator returns a list of URLs)
                    if isinstance(output, list) and len(output) > 0:
                        image_url = output[0]  # Take first URL
                        elapsed = (datetime.now() - start_time).total_seconds()
                        logger.info(f"RunPod job completed in {elapsed:.1f}s")
                        logger.info(f"Image URL: {image_url}")
                        return image_url

                    # Handle dict output (legacy format)
                    if isinstance(output, dict):
                        if "error" in output:
                            logger.error(f"Job completed with error: {output['error']}")
                            return None

                        image_url = output.get("image_url")
                        if image_url:
                            elapsed = (datetime.now() - start_time).total_seconds()
                            logger.info(f"RunPod job completed in {elapsed:.1f}s")
                            logger.info(f"Image URL: {image_url}")
                            return image_url

                    logger.error(f"Unexpected output format: {type(output)} - {output}")
                    return None

                elif status in ["FAILED", "CANCELLED"]:
                    error = data.get("error", "Unknown error")
                    logger.error(f"Job {status}: {error}")
                    return None

                elif status in ["IN_QUEUE", "IN_PROGRESS"]:
                    await asyncio.sleep(interval_sec)

                else:
                    logger.warning(f"Unknown status: {status}")
                    await asyncio.sleep(interval_sec)

            except Exception as e:
                logger.error(f"Error polling job (attempt {attempt}): {e}")
                if attempt < max_attempts:
                    await asyncio.sleep(interval_sec)
                else:
                    return None

    logger.error(f"Job timed out after {max_attempts * interval_sec / 60:.1f} minutes")
    return None


# Utility function for testing/debugging
async def test_runpod_generation():
    """
    Test function to verify RunPod generation works.
    This can be used for debugging or integration testing.
    """
    test_reference_url = "https://s3-api.dev.iron-mind.ai/faces/female/image_20250129_123750_610.jpg"
    test_gender = "f"
    test_ethnicity = "Swedish"

    logger.info("Testing RunPod base face generation...")
    base_face = await generate_runpod_base_face(
        reference_face_url=test_reference_url,
        gender=test_gender,
        ethnicity=test_ethnicity,
        save_debug=True
    )

    if base_face:
        logger.info("RunPod generation successful!")
        return True

    return False
