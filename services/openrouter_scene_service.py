"""
OpenRouter Scene-Based Image Generation Service
Replaces SeeDream with OpenRouter's Nano Banana 2 (Gemini 3.1 Flash Image Preview)
for scene-based image generation with dual image references.
"""

import os
import httpx
import logging
import base64
import asyncio
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'
OPENROUTER_SCENE_MODEL = os.getenv('OPENROUTER_SCENE_MODEL', 'google/gemini-3.1-flash-image-preview')
OPENROUTER_TIMEOUT = 180  # 3 minutes timeout for scene generation


async def generate_scene_image_openrouter(
    prompt: str,
    scene_image_url: str,
    person_image_url: str,
    size: str = "2560x1440",
    max_retries: int = 3
) -> Optional[bytes]:
    """
    Generate an image using OpenRouter's Nano Banana 2 (Gemini 3.1 Flash Image Preview)
    with dual image references for scene-based generation.

    This replaces SeeDream's img2img endpoint for the scene-based workflow.
    Uses dual image references: scene background + person's face.

    Args:
        prompt: Text prompt (e.g., "Replace the subject from image 1 with the subject from image 2")
        scene_image_url: URL of the scene background image (Image 1)
        person_image_url: URL of the person's base face image (Image 2)
        size: Desired image size (default: "2560x1440")
              Note: Gemini may adjust aspect ratio based on input images
        max_retries: Maximum number of retry attempts (default: 3)

    Returns:
        bytes: Generated image as bytes (PNG format), or None if generation fails

    Raises:
        Exception: If API call fails after all retries
    """
    try:
        # Validate configuration
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")

        logger.info(f"Generating scene image with OpenRouter Nano Banana 2")
        logger.info("=" * 80)
        logger.info(f"PROMPT: {prompt}")
        logger.info(f"MODEL: {OPENROUTER_SCENE_MODEL}")
        logger.info(f"Scene image (Image 1): {scene_image_url[:80]}...")
        logger.info(f"Person image (Image 2): {person_image_url[:80]}...")
        logger.info(f"Target size: {size}")
        logger.info("=" * 80)

        # Fetch both images to convert to base64
        # Set explicit timeout for image downloads (30s connect, 60s read)
        download_timeout = httpx.Timeout(60.0, connect=30.0)
        async with httpx.AsyncClient(timeout=download_timeout) as client:
            logger.info("Downloading scene and person images for base64 encoding...")

            # Download scene image
            scene_response = await client.get(scene_image_url)
            if scene_response.status_code != 200:
                raise Exception(f"Failed to download scene image: {scene_response.status_code}")
            scene_base64 = base64.b64encode(scene_response.content).decode('utf-8')

            # Download person image
            person_response = await client.get(person_image_url)
            if person_response.status_code != 200:
                raise Exception(f"Failed to download person image: {person_response.status_code}")
            person_base64 = base64.b64encode(person_response.content).decode('utf-8')

            logger.info(f"✓ Downloaded and encoded images (scene: {len(scene_response.content)} bytes, person: {len(person_response.content)} bytes)")

        # Prepare request headers
        headers = {
            'Authorization': f'Bearer {OPENROUTER_API_KEY}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://avatar-data-generator.dev.iron-mind.ai',
            'X-Title': 'Avatar Data Generator - Scene Generation'
        }

        # Prepare request payload with dual image references
        # Gemini expects images as inline data in the content array
        payload = {
            'model': OPENROUTER_SCENE_MODEL,
            'messages': [{
                'role': 'user',
                'content': [
                    {
                        'type': 'text',
                        'text': prompt
                    },
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': f'data:image/png;base64,{scene_base64}'
                        }
                    },
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': f'data:image/png;base64,{person_base64}'
                        }
                    }
                ]
            }],
            'modalities': ['image'],  # Request image output
            'temperature': 0.7  # Some randomness for variation
        }

        # Attempt generation with retries
        for attempt in range(1, max_retries + 1):
            try:
                # Configure explicit timeout for all operations (connect, read, write, pool)
                timeout = httpx.Timeout(OPENROUTER_TIMEOUT, connect=30.0)
                async with httpx.AsyncClient(timeout=timeout) as client:
                    logger.info(f"Attempt {attempt}/{max_retries}: Calling OpenRouter API...")

                    response = await client.post(
                        OPENROUTER_API_URL,
                        headers=headers,
                        json=payload
                    )

                    # Check for HTTP errors
                    if response.status_code != 200:
                        error_detail = response.json() if response.text else {'error': 'Unknown error'}
                        logger.error(f"OpenRouter API HTTP error on attempt {attempt}: {response.status_code} - {error_detail}")

                        if attempt < max_retries:
                            logger.info(f"Retrying in 3 seconds...")
                            await asyncio.sleep(3)
                            continue
                        else:
                            raise Exception(f"OpenRouter API error: {response.status_code} - {error_detail}")

                    # Parse response
                    result = response.json()
                    logger.debug(f"OpenRouter response: {result}")

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

                    # Parse base64 data
                    # Format: "data:image/png;base64,{base64_string}"
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

                    logger.info(f"✓ Successfully generated scene image with OpenRouter")
                    logger.info(f"  Image size: {len(image_bytes)} bytes")

                    return image_bytes

            except httpx.TimeoutException:
                logger.error(f"OpenRouter API timeout on attempt {attempt}")
                if attempt < max_retries:
                    logger.info(f"Retrying in 3 seconds...")
                    await asyncio.sleep(3)
                    continue
                else:
                    raise Exception("OpenRouter API timeout after all retries")

            except Exception as e:
                logger.error(f"Error on attempt {attempt}: {str(e)}")
                if attempt < max_retries:
                    logger.info(f"Retrying in 3 seconds...")
                    await asyncio.sleep(3)
                    continue
                else:
                    raise

        return None

    except Exception as e:
        logger.error(f"OpenRouter scene image generation failed: {str(e)}")
        raise


async def test_openrouter_scene():
    """Test function to verify OpenRouter scene generation works"""
    print("\n" + "=" * 80)
    print("TESTING OPENROUTER NANO BANANA 2 SCENE GENERATION")
    print("=" * 80)

    # Use test images
    scene_url = "https://s3-api.dev.iron-mind.ai/avatar-images/test-images/base-scene.png"
    person_url = "https://s3-api.dev.iron-mind.ai/avatar-images/test-images/base-person.png"
    prompt = "Replace the subject from image 1 with the subject from image 2"

    print(f"Scene image: {scene_url}")
    print(f"Person image: {person_url}")
    print(f"Prompt: {prompt}")

    try:
        image_bytes = await generate_scene_image_openrouter(
            prompt=prompt,
            scene_image_url=scene_url,
            person_image_url=person_url
        )

        if image_bytes:
            print(f"\n✅ SUCCESS! Generated scene image: {len(image_bytes)} bytes")

            # Save to file
            output_path = '/tmp/openrouter_scene_test.png'
            with open(output_path, 'wb') as f:
                f.write(image_bytes)
            print(f"Saved to: {output_path}")
        else:
            print("\n❌ FAILED: No image generated")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(test_openrouter_scene())
