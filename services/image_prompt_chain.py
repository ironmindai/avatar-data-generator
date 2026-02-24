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
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Import workflow logger
from services.workflow_logger import create_workflow_logger

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
        prompts_history: Optional[List[str]] = None,
        task_id: Optional[int] = None,
        persona_id: Optional[int] = None
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
            task_id: Optional GenerationTask.id for workflow logging
            persona_id: Optional GenerationResult.id for workflow logging

        Returns:
            Tuple of (final_prompts, image_ideas):
                - final_prompts: List of complete prompts ready for image generation
                - image_ideas: List of raw image ideas (for history tracking)
        """
        # Start workflow logging
        async with create_workflow_logger(
            workflow_name='image_prompt_chain',
            task_id=task_id,
            persona_id=persona_id
        ) as wf_logger:
            try:
                # Log input data
                wf_logger.set_input({
                    'person_data': person_data,
                    'num_images': num_images,
                    'prompts_history': prompts_history,
                    'prompts_history_count': len(prompts_history) if prompts_history else 0
                })

                logger.info(f"Generating {num_images} image prompts for {person_data.get('firstname')} {person_data.get('lastname')}")

                # Validate person data
                required_fields = ['firstname', 'lastname', 'gender', 'bio_facebook']
                missing = [f for f in required_fields if f not in person_data]
                if missing:
                    raise ValueError(f"Missing required person data: {missing}")

                # Initialize context
                generated_ideas = prompts_history or []
                final_prompts = []

                # Realistic social media mix (dynamic based on num_images)
                # Selfies: ~25% (1-2 max), Candid/friend photos: ~50%, Group photos: ~25%
                import random

                image_types = []
                if num_images <= 4:
                    # For 4 images: 1 selfie, 2 candid, 1 group
                    image_types = ['selfie', 'candid', 'candid', 'group']
                elif num_images <= 6:
                    # For 5-6 images: 1 selfie, 3-4 candid, 1 group
                    image_types = ['selfie'] + ['candid'] * (num_images - 2) + ['group']
                else:
                    # For 7+ images: 2 selfies, rest split between candid and group
                    num_selfies = 2
                    num_groups = max(1, num_images // 4)  # ~25% groups
                    num_candid = num_images - num_selfies - num_groups
                    image_types = ['selfie'] * num_selfies + ['candid'] * num_candid + ['group'] * num_groups

                # Shuffle to randomize order (except keep first image as selfie for consistency)
                first = image_types[0]
                rest = image_types[1:]
                random.shuffle(rest)
                image_types = [first] + rest

                logger.info(f"Image type distribution: {image_types}")

                # Generate each prompt sequentially
                for i in range(num_images):
                    image_type = image_types[i]

                    # Map to description for LLM
                    if image_type == 'selfie':
                        image_desc = "selfie taken by the person"
                    elif image_type == 'candid':
                        image_desc = "casual photo taken by a friend during an activity"
                    else:  # group
                        image_desc = "photo with other people (friends, family, or colleagues)"

                    logger.info(f"Generating prompt {i+1}/{num_images} ({image_type})...")

                    # Step 1: Generate image idea
                    idea = await self._generate_idea(
                        person_data=person_data,
                        image_type=image_desc,
                        previous_ideas=generated_ideas,
                        wf_logger=wf_logger,
                        node_order=i * 3  # Each image has 3 nodes
                    )

                    logger.debug(f"Generated idea: {idea}")

                    # Step 2: Compose structured prompt
                    structured_prompt = await self._compose_structured_prompt(
                        person_data=person_data,
                        image_idea=idea,
                        image_number=i + 1,
                        is_selfie=(image_type == 'selfie'),
                        wf_logger=wf_logger,
                        node_order=i * 3 + 1
                    )

                    logger.debug(f"Structured prompt: {structured_prompt}")

                    # Step 3: Add dual-reference suffix
                    final_prompt = await self._add_dual_reference_suffix(
                        structured_prompt=structured_prompt,
                        image_type=image_type,
                        wf_logger=wf_logger,
                        node_order=i * 3 + 2
                    )

                    logger.info(f"Final prompt {i+1}: {final_prompt[:100]}...")

                    # Add to history and results
                    generated_ideas.append(idea)
                    final_prompts.append(final_prompt)

                logger.info(f"Successfully generated {len(final_prompts)} image prompts with {len(generated_ideas)} ideas")

                # Log output data
                wf_logger.set_output({
                    'final_prompts': final_prompts,
                    'image_ideas': generated_ideas,
                    'prompts_generated': len(final_prompts),
                    'ideas_generated': len(generated_ideas)
                })

                return final_prompts, generated_ideas

            except Exception as e:
                logger.error(f"Error generating image prompts: {str(e)}", exc_info=True)
                raise

    async def _generate_idea(
        self,
        person_data: Dict[str, any],
        image_type: str,
        previous_ideas: List[str],
        wf_logger=None,
        node_order: int = 0
    ) -> str:
        """
        Step 1: Generate a single image idea.

        Equivalent to Flowise "Generate Ideas" node (llmAgentflow_0).
        """
        # Start node logging
        node_logger = wf_logger.start_node(
            node_name='generate_idea',
            order=node_order,
            input_data={
                'person_name': f"{person_data['firstname']} {person_data['lastname']}",
                'image_type': image_type,
                'previous_ideas_count': len(previous_ideas)
            }
        ) if wf_logger else None

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

            # Log LLM call details
            if node_logger:
                node_logger.log_llm_call(
                    model=LLM_MODEL,
                    temperature=LLM_TEMPERATURE,
                    max_tokens=200,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    response=idea,
                    usage={
                        'prompt_tokens': response.usage.prompt_tokens,
                        'completion_tokens': response.usage.completion_tokens,
                        'total_tokens': response.usage.total_tokens
                    }
                )
                node_logger.complete(
                    status='completed',
                    output_data={'idea': idea}
                )

            return idea

        except Exception as e:
            logger.error(f"Error generating idea: {str(e)}")
            if node_logger:
                node_logger.complete(status='failed', error_message=str(e))
            raise

    async def _compose_structured_prompt(
        self,
        person_data: Dict[str, any],
        image_idea: str,
        image_number: int,
        is_selfie: bool = True,
        wf_logger=None,
        node_order: int = 1
    ) -> str:
        """
        Step 2: Compose a SHORT, SIMPLE prompt from the idea.

        Equivalent to Flowise "Final Prompt" node (llmAgentflow_1).
        Generates concise, natural descriptions that work better with SeeDream.
        """
        # Start node logging
        node_logger = wf_logger.start_node(
            node_name='compose_structured_prompt',
            order=node_order,
            input_data={
                'image_idea': image_idea,
                'image_number': image_number,
                'is_selfie': is_selfie
            }
        ) if wf_logger else None

        try:
            # System prompt with SHORT examples
            system_prompt = (
                "You are to generate a SHORT, SIMPLE scene description for image generation. "
                "Keep it to ONE sentence describing the activity/setting. Be concise and natural.\n\n"
                "Here are examples:\n\n"
                "<EXAMPLES>\n"
                "taking a mirror selfie in a bathroom\n"
                "sitting at a coffee shop with a laptop\n"
                "at the gym after a workout\n"
                "walking on a beach trail\n"
                "at home on the couch\n"
                "at a park on a sunny day\n"
                "</EXAMPLES>\n\n"
                "CRITICAL GUARDRAILS:\n"
                "- ONE simple sentence only\n"
                "- Describe activity and location ONLY\n"
                "- NO clothing details, NO hair descriptions, NO background details\n"
                "- NO quality descriptors\n"
                "- Keep it under 15 words\n"
                "- ABSOLUTELY NO mentions of: camera, phone, mobile, lens, photograph, taking photo, smartphone, device, screen\n"
                "- For selfies, NEVER mention the camera/phone - it's implied by 'selfie'\n\n"
                "Output ONLY the simple scene description, nothing else."
            )

            # User prompt
            user_prompt = (
                f"Image idea: {image_idea}\n\n"
                "Generate a short, simple scene description."
            )

            # Call LLM
            response = await self.client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=LLM_TEMPERATURE,
                max_tokens=100
            )

            structured_prompt = response.choices[0].message.content.strip()

            # Log LLM call details
            if node_logger:
                node_logger.log_llm_call(
                    model=LLM_MODEL,
                    temperature=LLM_TEMPERATURE,
                    max_tokens=100,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    response=structured_prompt,
                    usage={
                        'prompt_tokens': response.usage.prompt_tokens,
                        'completion_tokens': response.usage.completion_tokens,
                        'total_tokens': response.usage.total_tokens
                    }
                )
                node_logger.complete(
                    status='completed',
                    output_data={'structured_prompt': structured_prompt}
                )

            return structured_prompt

        except Exception as e:
            logger.error(f"Error composing structured prompt: {str(e)}")
            if node_logger:
                node_logger.complete(status='failed', error_message=str(e))
            raise

    async def _add_dual_reference_suffix(
        self,
        structured_prompt: str,
        image_type: str = 'selfie',
        wf_logger=None,
        node_order: int = 2
    ) -> str:
        """
        Step 3: Add dual-reference suffix using Format 2 from matrix tests.

        Format 2 (winner): "The person in image 1 is {activity}. This is an amateur social media photo based on the quality and style of image 2."

        Args:
            structured_prompt: The simple scene description
            image_type: 'selfie', 'candid', or 'group'

        This format produced the best results in playground testing with natural, concise prompts.
        Uses POSITIVE quality descriptors (amateur, casual, poor lighting) rather than negatives.
        """
        # Start node logging
        node_logger = wf_logger.start_node(
            node_name='add_dual_reference_suffix',
            order=node_order,
            input_data={
                'structured_prompt': structured_prompt,
                'image_type': image_type
            }
        ) if wf_logger else None

        try:
            # Build natural prompt with Format 2 structure + positive amateur quality descriptors
            if image_type == 'selfie':
                final_prompt = (
                    f"The person in image 1 is taking a selfie - {structured_prompt}. "
                    f"This is an amateur social media photo based on the quality and style of image 2. "
                    f"Poor lighting, casual amateur quality, unpolished, grainy, low resolution."
                )
            elif image_type == 'candid':
                final_prompt = (
                    f"The person in image 1 is {structured_prompt}. "
                    f"This is a casual photo taken by a friend, based on the quality and style of image 2. "
                    f"Amateur quality, bad lighting, spontaneous moment, unposed, grainy."
                )
            else:  # group
                final_prompt = (
                    f"The person in image 1 is {structured_prompt}. "
                    f"This is an amateur social media photo with friends based on the quality and style of image 2. "
                    f"Casual group shot, poor lighting, amateur quality, candid moment, unpolished."
                )

            logger.debug(f"Final prompt with dual-reference ({image_type}): {final_prompt}")

            # Log node completion (no LLM call, just string formatting)
            if node_logger:
                node_logger.complete(
                    status='completed',
                    output_data={'final_prompt': final_prompt}
                )

            return final_prompt

        except Exception as e:
            logger.error(f"Error adding dual-reference suffix: {str(e)}")
            if node_logger:
                node_logger.complete(status='failed', error_message=str(e))
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
