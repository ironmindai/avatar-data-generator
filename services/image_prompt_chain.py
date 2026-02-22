"""
Image Prompt Generation Chain
Generates individual image prompts using local LLM with context history.

This service replaces the Flowise workflow for generating image prompts
for the 4 additional images (after base image). It uses a multi-step LLM
chain to generate creative, non-repetitive image ideas.
"""

import os
import json
import logging
from typing import List, Dict, Optional
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
LLM_MODEL = "gpt-4o-mini"  # Fast and cost-effective for prompt generation
LLM_TEMPERATURE = 0.7  # Balanced creativity


class ImagePromptChain:
    """
    LLM chain for generating image prompts one by one with context awareness.

    This replaces the 3-step Flowise workflow:
    1. Generate idea for single image
    2. Compose structured prompt
    3. Add dual-reference suffix for SeeDream (Format 1 approach)
    """

    def __init__(self):
        """Initialize the OpenAI client."""
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        logger.info("ImagePromptChain initialized")

    async def generate_image_prompts(
        self,
        person_data: Dict[str, any],
        num_images: int = 4,
        prompts_history: Optional[List[str]] = None
    ) -> tuple[List[str], List[str]]:
        """
        Generate N image prompts sequentially with context awareness.

        Args:
            person_data: Dictionary containing:
                - firstname: Person's first name
                - lastname: Person's last name
                - gender: 'm' or 'f'
                - bio_facebook: Facebook bio
                - bio_instagram: Instagram bio (optional)
                - ethnicity: Ethnicity (optional)
                - age: Age (optional)
            num_images: Number of image prompts to generate (default: 4)
            prompts_history: Optional list of previously used image ideas to avoid

        Returns:
            Tuple of (final_prompts, image_ideas):
                - final_prompts: List of complete prompts ready for image generation
                - image_ideas: List of raw image ideas (for history tracking)
        """
        try:
            logger.info(f"Generating {num_images} image prompts for {person_data.get('firstname')} {person_data.get('lastname')}")

            # Validate person data
            required_fields = ['firstname', 'lastname', 'gender', 'bio_facebook']
            missing = [f for f in required_fields if f not in person_data]
            if missing:
                raise ValueError(f"Missing required person data: {missing}")

            # Initialize context
            generated_ideas = prompts_history or []
            final_prompts = []

            # Determine selfie/group split (3 selfies + 1 group photo)
            selfie_count = num_images - 1
            group_count = 1

            # Generate each prompt sequentially
            for i in range(num_images):
                is_selfie = i < selfie_count
                image_type = "selfie" if is_selfie else "photo with other people"

                logger.info(f"Generating prompt {i+1}/{num_images} ({image_type})...")

                # Step 1: Generate image idea
                idea = await self._generate_idea(
                    person_data=person_data,
                    image_type=image_type,
                    previous_ideas=generated_ideas
                )

                logger.debug(f"Generated idea: {idea}")

                # Step 2: Compose structured prompt
                structured_prompt = await self._compose_structured_prompt(
                    person_data=person_data,
                    image_idea=idea,
                    image_number=i + 1,
                    is_selfie=is_selfie
                )

                logger.debug(f"Structured prompt: {structured_prompt}")

                # Step 3: Add dual-reference suffix
                final_prompt = await self._add_dual_reference_suffix(
                    structured_prompt=structured_prompt,
                    is_selfie=is_selfie
                )

                logger.info(f"Final prompt {i+1}: {final_prompt[:100]}...")

                # Add to history and results
                generated_ideas.append(idea)
                final_prompts.append(final_prompt)

            logger.info(f"Successfully generated {len(final_prompts)} image prompts with {len(generated_ideas)} ideas")
            return final_prompts, generated_ideas

        except Exception as e:
            logger.error(f"Error generating image prompts: {str(e)}", exc_info=True)
            raise

    async def _generate_idea(
        self,
        person_data: Dict[str, any],
        image_type: str,
        previous_ideas: List[str]
    ) -> str:
        """
        Step 1: Generate a single image idea.

        Equivalent to Flowise "Generate Ideas" node (llmAgentflow_0).
        """
        try:
            # Build person description
            name = f"{person_data['firstname']} {person_data['lastname']}"
            gender = 'male' if person_data['gender'].lower() == 'm' else 'female'
            bio = person_data['bio_facebook']

            # Add optional fields
            extras = []
            if person_data.get('ethnicity'):
                extras.append(f"Ethnicity: {person_data['ethnicity']}")
            if person_data.get('age'):
                extras.append(f"Age: {person_data['age']}")

            person_info = f"Name: {name}, Gender: {gender}, Bio: {bio}"
            if extras:
                person_info += ", " + ", ".join(extras)

            # Build history context
            history_context = ""
            if previous_ideas:
                history_context = f"\n\nIdeas already used (DO NOT repeat these):\n" + "\n".join(f"- {idea}" for idea in previous_ideas)

            # System prompt
            system_prompt = (
                "You are to come up with an idea for 1 image of this social media person. "
                "The image should be a day-to-day life photo of the person. "
                "They are NOT an influencer, so pretty boring stuff just to reflect an average person "
                "and their interests, occupation, or activities that relate to their info.\n\n"
                "The image MUST have different clothes and never repeat same pose and/or facial expression - "
                "so that should implicitly be described. Avoid smiling in all images, be creative!\n\n"
                "Output ONLY the image idea description, nothing else."
            )

            # User prompt
            user_prompt = (
                f"Person information:\n{person_info}\n\n"
                f"Generate 1 {image_type} idea.{history_context}"
            )

            # Call LLM
            response = await self.client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=LLM_TEMPERATURE,
                max_tokens=200
            )

            idea = response.choices[0].message.content.strip()
            return idea

        except Exception as e:
            logger.error(f"Error generating idea: {str(e)}")
            raise

    async def _compose_structured_prompt(
        self,
        person_data: Dict[str, any],
        image_idea: str,
        image_number: int,
        is_selfie: bool = True
    ) -> str:
        """
        Step 2: Compose a structured prompt from the idea.

        Equivalent to Flowise "Final Prompt" node (llmAgentflow_1).
        """
        try:
            gender = 'male' if person_data['gender'].lower() == 'm' else 'female'
            age_str = str(person_data.get('age', 'unknown age'))

            # System prompt with example (NEUTRAL - no quality descriptors)
            # Note: POV selfie prefix will be added in step 3 (_add_dual_reference_suffix)
            system_prompt = (
                "You are to generate a NEUTRAL scene description for image generation. "
                "Do NOT add any quality descriptors, lighting details, or camera type - those will be added later.\n\n"
                "Here is an example for the structure:\n\n"
                "<EXAMPLE>\n"
                f"{age_str} year old {gender}. mirror selfie trying on clothes in a dressing room\n"
                "</EXAMPLE>\n\n"
                "GUARDRAILS:\n"
                "- Describe the scene, pose, and activity ONLY\n"
                "- Do NOT add quality descriptors like 'casual', 'amateur', 'low quality', etc.\n"
                "- Do NOT add lighting or camera details\n"
                "- Do NOT add 'POV selfie' prefix - that will be added automatically\n\n"
                "Keep it simple and neutral. Quality/aesthetic will be added in next step.\n\n"
                "Output ONLY the neutral scene description, nothing else."
            )

            # User prompt
            user_prompt = (
                f"Person: {age_str} year old {gender}\n"
                f"Image idea: {image_idea}\n\n"
                "Compose a neutral scene description (no quality descriptors)."
            )

            # Call LLM
            response = await self.client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=LLM_TEMPERATURE,
                max_tokens=300
            )

            structured_prompt = response.choices[0].message.content.strip()
            return structured_prompt

        except Exception as e:
            logger.error(f"Error composing structured prompt: {str(e)}")
            raise

    async def _add_dual_reference_suffix(
        self,
        structured_prompt: str,
        is_selfie: bool = True
    ) -> str:
        """
        Step 3: Add dual-reference suffix for SeeDream.

        Format 1 (winner from matrix tests):
        "{description}. The subject is in image 1 and the quality and lighting is based on image 2."

        For selfie images, also adds "POV selfie" prefix to establish camera perspective.
        """
        try:
            # Add POV selfie prefix if it's a selfie and not already present
            if is_selfie and not structured_prompt.lower().startswith('pov selfie'):
                structured_prompt = f"POV selfie. {structured_prompt}"

            # Add dual-reference suffix
            final_prompt = f"{structured_prompt}. The subject is in image 1 and the quality and lighting is based on image 2."

            logger.debug(f"Final prompt with dual-reference suffix: {final_prompt[:200]}...")

            return final_prompt

        except Exception as e:
            logger.error(f"Error adding dual-reference suffix: {str(e)}")
            raise


# Singleton instance
_prompt_chain = None


def get_prompt_chain() -> ImagePromptChain:
    """Get or create the singleton ImagePromptChain instance."""
    global _prompt_chain
    if _prompt_chain is None:
        _prompt_chain = ImagePromptChain()
    return _prompt_chain


# Testing function
async def test_prompt_generation():
    """Test the prompt generation chain."""
    test_person_data = {
        'firstname': 'Sarah',
        'lastname': 'Chen',
        'gender': 'f',
        'bio_facebook': 'Software engineer who loves hiking, photography, and coffee. Living in Seattle.',
        'ethnicity': 'Asian',
        'age': 28
    }

    logger.info("Testing image prompt chain...")

    try:
        chain = get_prompt_chain()
        prompts = await chain.generate_image_prompts(test_person_data, num_images=4)

        logger.info(f"Generated {len(prompts)} prompts:")
        for i, prompt in enumerate(prompts, 1):
            logger.info(f"\nPrompt {i}:\n{prompt}\n")

        return True

    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False
