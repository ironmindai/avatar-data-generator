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
    3. Add natural quality refinements
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
    ) -> List[str]:
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
            prompts_history: Optional list of previously used prompts to avoid

        Returns:
            List of final image generation prompts
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
                    image_number=i + 1
                )

                logger.debug(f"Structured prompt: {structured_prompt}")

                # Step 3: Add natural quality refinements
                final_prompt = await self._add_natural_refinements(
                    structured_prompt=structured_prompt
                )

                logger.info(f"Final prompt {i+1}: {final_prompt[:100]}...")

                # Add to history and results
                generated_ideas.append(idea)
                final_prompts.append(final_prompt)

            logger.info(f"Successfully generated {len(final_prompts)} image prompts")
            return final_prompts

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
        image_number: int
    ) -> str:
        """
        Step 2: Compose a structured prompt from the idea.

        Equivalent to Flowise "Final Prompt" node (llmAgentflow_1).
        """
        try:
            gender = 'male' if person_data['gender'].lower() == 'm' else 'female'
            age_str = str(person_data.get('age', 'unknown age'))

            # System prompt with example
            system_prompt = (
                "You are to generate a prompt for image generation. We generate individual images.\n\n"
                "Here is an example for the structure:\n\n"
                "<EXAMPLE>\n"
                f"Generate an image of a 29 year old female, casual social media quality—not well-produced, "
                "amateur digital camera aesthetic, low resolution. Create a composition showing: "
                "mirror selfie trying on clothes in a dressing room\n"
                "</EXAMPLE>\n\n"
                "GUARDRAILS:\n"
                "- Don't generate mobile device in their hands on selfies unless they are involving a mirror\n"
                "- Face expressions and attire should be varied and unique\n"
                "- Keep the natural and amateur quality aesthetic\n\n"
                "The natural and amateur quality is a must to preserve and the wording in the example was tested and works well!\n\n"
                "Now you are going to be given the person's info and requested image idea, and you will compose the final prompt.\n\n"
                "Output ONLY the final prompt, nothing else."
            )

            # User prompt
            user_prompt = (
                f"Person: {age_str} year old {gender}\n"
                f"Image idea: {image_idea}\n\n"
                "Compose the prompt maintaining the guardrails."
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

    async def _add_natural_refinements(
        self,
        structured_prompt: str
    ) -> str:
        """
        Step 3: Add natural quality refinements to the prompt.

        Randomly selects one of 4 tested quality styles (E, D, B, A) and applies
        it to the structured prompt. These are quality modifiers that work
        regardless of the scene content.
        """
        try:
            import random

            # 4 winning quality styles from experimentation
            QUALITY_STYLES = {
                "style_a_ultra_amateur": {
                    "prefix": "Low quality phone camera photo. Shot on old smartphone camera, bad lighting, not professional.",
                    "suffix": "Realistic imperfections: motion blur from shaky hands, grainy sensor noise, awkward framing, bad angle, natural unflattering light"
                },
                "style_b_candid_unpolished": {
                    "prefix": "Candid unposed moment captured on phone camera.",
                    "suffix": "Not paying attention to camera. Natural everyday lighting, random background clutter visible, not photogenic angle, caught mid-motion, real authentic moment, imperfect composition"
                },
                "style_d_chaos_natural": {
                    "prefix": "Deliberately bad photo quality, opposite of Instagram aesthetic.",
                    "suffix": "No filters, no editing, straight from camera, unflattering fluorescent lights, weird shadows, awkward crop, finger partially visible in corner, background is messy, very relatable and human"
                },
                "style_e_low_effort": {
                    "prefix": "Quick snapshot taken without care or composition.",
                    "suffix": "Poor framing, subject not centered, amateur lighting from whatever source available, slightly blurry from movement, casual everyday moment captured hastily, very natural and unpolished"
                }
            }

            # Randomly select one quality style
            selected_style_id = random.choice(list(QUALITY_STYLES.keys()))
            selected_style = QUALITY_STYLES[selected_style_id]

            logger.info(f"Selected quality style: {selected_style_id}")

            # Build final prompt: PREFIX + structured_prompt + SUFFIX
            final_prompt = (
                f"{selected_style['prefix']} "
                f"{structured_prompt} "
                f"{selected_style['suffix']}"
            )

            logger.debug(f"Final prompt with quality modifiers: {final_prompt[:200]}...")

            return final_prompt

        except Exception as e:
            logger.error(f"Error adding natural refinements: {str(e)}")
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
