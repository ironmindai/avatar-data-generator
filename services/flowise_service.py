"""
Flowise Prompt Generation Service
Handles image prompt generation using Flowise workflow.

This module provides a function to generate image prompts for avatar creation
by calling a Flowise workflow that processes person data and creates detailed
prompts for image generation.
"""

import os
import json
import httpx
import logging
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Flowise Configuration
FLOWISE_PROMPT_WORKFLOW_URL = "https://flowise.electric-marinade.com/api/v1/prediction/5171a0ec-8235-4db6-bc08-b23e4e22e641"
FLOWISE_AUTH_TOKEN = "JJXI5CYV55QYkal9-uce7dyJfyKj3EeRkROOpBgxeO4"
FLOWISE_PROMPT_TIMEOUT = 120  # 2 minutes timeout (workflow takes ~20 seconds)


async def generate_image_prompt(person_data: Dict[str, str], prompts_history: Optional[str] = None) -> Optional[str]:
    """
    Generate image prompt from person data using Flowise workflow.

    This function calls the Flowise prompt generation workflow which analyzes
    person data (name, gender, bios) and creates a detailed prompt for image
    generation.

    Args:
        person_data: Dictionary containing person information with keys:
            - firstname: Person's first name
            - lastname: Person's last name
            - gender: Gender (e.g., 'm', 'f')
            - bio_facebook: Facebook bio text
            - bio_instagram: Instagram bio text
            - bio_x: X (Twitter) bio text
            - bio_tiktok: TikTok bio text
            - ethnicity: Ethnicity (optional)
            - age: Age (optional)
        prompts_history: Optional string containing previously used prompts
            to avoid repetition (e.g., "Ideas already used, to avoid: prompt1, prompt2")

    Returns:
        str: Generated image prompt, or None if generation fails

    Raises:
        Exception: If API call fails or returns invalid response

    Example:
        >>> person_data = {
        ...     'firstname': 'Logan',
        ...     'lastname': 'Fitzroy',
        ...     'gender': 'm',
        ...     'bio_facebook': 'I am a digital marketing strategist...',
        ...     'bio_instagram': 'Digital Marketing Strategist...',
        ...     'bio_x': 'Digital marketing strategist...',
        ...     'bio_tiktok': 'Digital marketing tips...'
        ... }
        >>> prompt = await generate_image_prompt(person_data)
        >>> print(prompt)
        'Generate 4 images of a 29 year old male, casual social media quality...'
    """
    try:
        # Validate required fields
        required_fields = ['firstname', 'lastname', 'gender', 'bio_facebook',
                          'bio_instagram', 'bio_x', 'bio_tiktok']
        missing_fields = [field for field in required_fields if field not in person_data]

        if missing_fields:
            logger.error(f"Missing required fields: {missing_fields}")
            raise ValueError(f"Missing required person data fields: {missing_fields}")

        logger.info(f"Generating image prompt for {person_data['firstname']} {person_data['lastname']}")
        if prompts_history:
            logger.info(f"Using prompts_history: {prompts_history}")

        # Prepare request payload
        # Per Flowise KB: parameters must be sent as startState.startAgentflow_0 array
        # The workflow expects a single "person_data" key containing the full object as JSON
        person_data_json = json.dumps({
            "firstname": person_data['firstname'],
            "lastname": person_data['lastname'],
            "gender": person_data['gender'],
            "bio_facebook": person_data['bio_facebook'],
            "bio_instagram": person_data['bio_instagram'],
            "bio_x": person_data['bio_x'],
            "bio_tiktok": person_data['bio_tiktok'],
            "ethnicity": person_data.get('ethnicity', ''),
            "age": person_data.get('age', None)
        })

        # Build startAgentflow_0 array with person_data and optional prompts_history
        start_agent_flow = [
            {"key": "person_data", "value": person_data_json}
        ]

        # Add prompts_history if provided
        if prompts_history:
            start_agent_flow.append({"key": "prompts_history", "value": prompts_history})

        payload = {
            "question": "go",
            "overrideConfig": {
                "startState": {
                    "startAgentflow_0": start_agent_flow
                }
            }
        }

        # Prepare headers
        headers = {
            "Authorization": f"Bearer {FLOWISE_AUTH_TOKEN}",
            "Content-Type": "application/json"
        }

        logger.debug(f"Calling Flowise workflow: {FLOWISE_PROMPT_WORKFLOW_URL}")
        logger.info("=" * 80)
        logger.info("FLOWISE PAYLOAD (for image prompt generation):")
        logger.info(json.dumps(payload, indent=2))
        logger.info("=" * 80)

        # Make async HTTP request to Flowise
        async with httpx.AsyncClient(timeout=FLOWISE_PROMPT_TIMEOUT) as client:
            response = await client.post(
                FLOWISE_PROMPT_WORKFLOW_URL,
                json=payload,
                headers=headers
            )

            # Check for errors
            response.raise_for_status()
            result = response.json()

            logger.debug(f"Flowise response received: {len(str(result))} chars")

            # Extract text field from response
            if 'text' not in result:
                logger.error("Response missing 'text' field")
                logger.error(f"Full response: {result}")
                raise Exception("Invalid Flowise response format: missing 'text' field")

            text_content = result['text']

            # Parse the JSON inside text to get final_prompt
            try:
                prompt_data = json.loads(text_content)

                if 'final_prompt' not in prompt_data:
                    logger.error("Parsed text missing 'final_prompt' field")
                    logger.error(f"Parsed content: {prompt_data}")
                    raise Exception("Invalid prompt data: missing 'final_prompt' field")

                final_prompt = prompt_data['final_prompt']

                logger.info(f"Successfully generated prompt ({len(final_prompt)} chars)")
                logger.info("=" * 80)
                logger.info("FLOWISE RESPONSE - FINAL_PROMPT:")
                logger.info(f"{final_prompt}")
                logger.info("=" * 80)

                return final_prompt

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse text field as JSON: {e}")
                logger.error(f"Text content: {text_content[:500]}...")
                raise Exception(f"Failed to parse Flowise response text as JSON: {str(e)}")

    except httpx.HTTPStatusError as e:
        error_detail = {}
        try:
            error_detail = e.response.json()
        except Exception:
            error_detail = {'text': e.response.text}

        logger.error(f"Flowise API HTTP error: {e.response.status_code} - {error_detail}")
        raise Exception(f"Flowise API error: {error_detail}")

    except httpx.TimeoutException:
        logger.error(f"Request timed out after {FLOWISE_PROMPT_TIMEOUT}s")
        raise Exception(f"Flowise prompt generation timed out after {FLOWISE_PROMPT_TIMEOUT}s")

    except ValueError as e:
        # Re-raise validation errors
        raise e

    except Exception as e:
        logger.error(f"Error generating image prompt: {str(e)}", exc_info=True)
        raise Exception(f"Image prompt generation failed: {str(e)}")


# Utility function for testing/debugging
async def test_prompt_generation():
    """
    Test function to verify prompt generation works.
    This can be used for debugging or integration testing.
    """
    test_person_data = {
        'firstname': 'Logan',
        'lastname': 'Fitzroy',
        'gender': 'm',
        'bio_facebook': 'I\'m Logan, a digital marketing strategist passionate about helping small businesses grow online. Based in Austin, I love BBQ and live music!',
        'bio_instagram': 'Digital Marketing Strategist\nHelping small businesses grow\nBBQ & live music aficionado\nBased in Austin, TX',
        'bio_x': 'Digital marketing strategist helping small businesses thrive. BBQ lover. Tweets about growth strategies and Austin life.',
        'bio_tiktok': 'Digital marketing tips and BBQ adventures from Austin!'
    }

    logger.info("Testing Flowise prompt generation...")

    try:
        prompt = await generate_image_prompt(test_person_data)

        if prompt:
            logger.info("Prompt generation successful!")
            logger.info(f"Generated prompt: {prompt}")
            return True
        else:
            logger.error("Prompt generation returned None")
            return False

    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False
