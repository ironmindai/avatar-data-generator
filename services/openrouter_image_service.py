"""
OpenRouter Image Generation Service
Provides image generation using OpenRouter's GPT-5 Image model as an alternative to OpenAI DALL-E.
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
OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'openai/gpt-5-image')
OPENROUTER_TIMEOUT = 120  # 2 minutes timeout


async def generate_image_openrouter(
    prompt: str,
    size: str = "1024x1024",
    max_retries: int = 3
) -> Optional[bytes]:
    """
    Generate an image using OpenRouter's GPT-5 Image model.

    OpenRouter provides access to GPT-5 Image which combines advanced language
    capabilities with state-of-the-art image generation featuring superior
    instruction following, text rendering, and detailed image editing.

    Args:
        prompt: Text prompt describing the desired image
        size: Image size (e.g., "1024x1024", "1024x1536", "1536x1024")
              Note: Size may be ignored depending on model capabilities
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

        logger.info(f"Generating image with OpenRouter GPT-5 Image")
        logger.info("=" * 80)
        logger.info(f"PROMPT: {prompt}")
        logger.info(f"MODEL: {OPENROUTER_MODEL}")
        logger.info(f"SIZE: {size}")
        logger.info("=" * 80)

        # Prepare request
        headers = {
            'Authorization': f'Bearer {OPENROUTER_API_KEY}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://avatar-data-generator.dev.iron-mind.ai',  # Optional but recommended
            'X-Title': 'Avatar Data Generator'  # Optional but recommended
        }

        payload = {
            'model': OPENROUTER_MODEL,
            'messages': [{
                'role': 'user',
                'content': prompt
            }],
            'modalities': ['image']  # Request image-only output
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
                            logger.info(f"Retrying in 2 seconds...")
                            await asyncio.sleep(2)
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

                    logger.info(f"Successfully generated image with OpenRouter")
                    logger.info(f"Image size: {len(image_bytes)} bytes")

                    return image_bytes

            except httpx.TimeoutException:
                logger.error(f"OpenRouter API timeout on attempt {attempt}")
                if attempt < max_retries:
                    logger.info(f"Retrying in 2 seconds...")
                    await asyncio.sleep(2)
                    continue
                else:
                    raise Exception("OpenRouter API timeout after all retries")

            except Exception as e:
                logger.error(f"Error on attempt {attempt}: {str(e)}")
                if attempt < max_retries:
                    logger.info(f"Retrying in 2 seconds...")
                    await asyncio.sleep(2)
                    continue
                else:
                    raise

        return None

    except Exception as e:
        logger.error(f"OpenRouter image generation failed: {str(e)}")
        raise


async def test_openrouter():
    """Test function to verify OpenRouter integration works"""
    import asyncio

    print("\n" + "=" * 80)
    print("TESTING OPENROUTER GPT-5 IMAGE GENERATION")
    print("=" * 80)

    prompt = "A candid photo of a person smiling at a cafe, amateur photography, natural lighting"

    try:
        image_bytes = await generate_image_openrouter(prompt)

        if image_bytes:
            print(f"\n✅ SUCCESS! Generated image: {len(image_bytes)} bytes")

            # Save to file
            output_path = '/tmp/openrouter_test.png'
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
    import asyncio
    asyncio.run(test_openrouter())
