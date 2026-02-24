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
    3. Create clean prompt for two-stage SeeDream workflow
       - Stage 1: Clean image generation (base-face only)
       - Stage 2: Degradation applied via style_degradation_prompts.py
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

                    logger.info(f"Clean prompt {i+1}: {final_prompt[:100]}...")

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
                "The image should be a MESSY, CANDID, UNFLATTERING day-to-day life photo. "
                "They are NOT an influencer - this is an AUTHENTICALLY AMATEUR social media photo.\n\n"
                "UNFLATTERING/MESSY MOMENT EXAMPLES:\n"
                "- Awkward timing: mid-chew, yawning, scratching, adjusting clothes, mid-sentence\n"
                "- Unflattering poses: slouched posture, messy hair, just woke up, lying down awkwardly\n"
                "- Chaotic environments: unmade bed, messy room, cluttered desk, dirty mirror, laundry visible\n"
                "- Caught off-guard: distracted look, looking away from camera, mouth open, eyes half-closed\n\n"
                "The image MUST have different clothes and never repeat same pose and/or facial expression. "
                "Avoid smiling in all images, be creative with REAL human moments (bored, tired, distracted).\n\n"
                "Output ONLY the image idea description with messy/unflattering elements, nothing else."
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
            # System prompt with examples that include attire and pose
            system_prompt = (
                "You are to generate a MESSY, AMATEUR, CANDID scene description for social media photo generation. "
                "Include the activity, location, clothing/attire, pose, expression, AND amateur photo flaws. "
                "This should look like a REAL social media photo, not a professional shot.\n\n"
                "Here are examples of GOOD amateur photos:\n\n"
                "<EXAMPLES>\n"
                "slouched on couch eating pizza, messy hair, wearing old t-shirt and sweatpants, mouth open mid-chew, blurry, clothes on floor in background\n"
                "taking bathroom mirror selfie, finger partially in shot, messy sink visible, wearing pajamas, hair unbrushed, awkward angle\n"
                "sitting at desk with laptop, off-center in frame, messy papers everywhere, wearing hoodie, looking away from camera, distracted\n"
                "lying on unmade bed scrolling phone, wearing wrinkled t-shirt, awkward angle from above, yawning, messy room visible\n"
                "at gym locker room mirror, towel around neck, sweaty and exhausted, bad overhead lighting, other people's stuff in background\n"
                "in car taking selfie, one hand on steering wheel, squinting from sun, fast food bag on passenger seat, slightly blurry\n"
                "standing in messy kitchen, wearing tank top and shorts, mid-sentence with mouth open, dirty dishes in sink behind, awkward pose\n"
                "</EXAMPLES>\n\n"
                "AMATEUR PHOTO REQUIREMENTS (MUST INCLUDE 2-3 OF THESE):\n"
                "- Technical flaws: blurry, finger in shot, awkward angle, bad framing, poorly centered, off-center, bad lighting\n"
                "- Environmental mess: messy background, cluttered room, unmade bed, dirty mirror, stuff on floor, messy desk, visible clutter\n"
                "- Poor composition: awkward angle, bad framing, off-center, too close, weird perspective\n"
                "- Human mess: slouched posture, messy hair, unbrushed hair, wrinkled clothes, mid-action, unflattering pose\n"
                "- Caught moments: mid-chew, yawning, looking away, distracted, mouth open, eyes half-closed, awkward expression\n\n"
                "CRITICAL REQUIREMENTS:\n"
                "- Include: activity, location, clothing/attire, pose, expression, AND 2-3 amateur photo flaws\n"
                "- MUST include environmental mess OR technical flaws in EVERY description\n"
                "- Clothing should be casual/worn/wrinkled (old t-shirts, sweatpants, pajamas, hoodies)\n"
                "- Pose should be natural/slouched/awkward (not posed or flattering)\n"
                "- Expression should be authentic (bored, tired, distracted, mid-action, NOT smiling)\n"
                "- EXCLUDE: quality descriptors like 'professional', 'well-lit', 'high-quality'\n"
                "- Keep it under 30 words (extra 5 words for amateur details)\n"
                "- ABSOLUTELY NO mentions of: camera, phone, mobile, lens, photograph, taking photo, smartphone, device, screen\n"
                "- For selfies, NEVER mention the camera/phone - it's implied by 'selfie'\n\n"
                "Output ONLY the scene description with attire/pose/expression/amateur flaws, nothing else."
            )

            # User prompt
            user_prompt = (
                f"Image idea: {image_idea}\n\n"
                "Generate a scene description that includes activity, location, clothing, pose, and expression. "
                "Remove any atmospheric or background environment details."
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
        Step 3: Create clean single-reference prompt for two-stage degradation workflow.

        NEW WORKFLOW:
        Stage 1: Generate clean image from base-face using THIS prompt (no style degradation)
        Stage 2: Apply degradation to clean image using style_degradation_prompts.py

        This function now generates a clean, simple prompt that focuses on:
        1. The person from the base image
        2. The scene/activity/clothing/pose
        3. NO quality/style descriptors (those come from Stage 2 degradation)

        Args:
            structured_prompt: The scene description with attire/pose/expression
            image_type: 'selfie', 'candid', or 'group'
        """
        # Start node logging
        node_logger = wf_logger.start_node(
            node_name='add_clean_prompt_prefix',
            order=node_order,
            input_data={
                'structured_prompt': structured_prompt,
                'image_type': image_type
            }
        ) if wf_logger else None

        try:
            # Build clean prompt WITHOUT any quality/style descriptors
            # Quality will be applied in Stage 2 via degradation prompts
            if image_type == 'selfie':
                final_prompt = (
                    f"The person from the base image is taking a selfie - {structured_prompt}. "
                    f"Use the person's face and identity from the base image."
                )
            elif image_type == 'candid':
                final_prompt = (
                    f"The person from the base image is {structured_prompt}. "
                    f"Use the person's face and identity from the base image."
                )
            else:  # group
                final_prompt = (
                    f"The person from the base image is {structured_prompt}. "
                    f"Use the person's face and identity from the base image."
                )

            logger.debug(f"Final clean prompt ({image_type}): {final_prompt}")

            # Log node completion (no LLM call, just string formatting)
            if node_logger:
                node_logger.complete(
                    status='completed',
                    output_data={'final_prompt': final_prompt}
                )

            return final_prompt

        except Exception as e:
            logger.error(f"Error creating clean prompt: {str(e)}")
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
