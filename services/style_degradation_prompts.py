"""
Style Degradation Prompts
Collection of diverse "bad quality" prompts for Stage 2 image-to-image generation.

These prompts are used to apply realistic amateur/candid photo characteristics
to clean generated images, creating variety in lighting, camera quality, and
technical issues that make photos look authentically casual/unpolished.

Architecture: BASE_COMPRESSION_PREFIX + random(SPECIFIC_DEGRADATION)
Every image gets the foundational old social media compression quality,
plus a specific lighting/camera issue for variety.
"""

import random
import logging

logger = logging.getLogger(__name__)


# Base compression layer applied to ALL images
# Establishes foundational 2014-2016 social media photo quality
BASE_COMPRESSION_PREFIX = (
    "2014-2016 old social media photo quality: heavy JPEG compression artifacts, "
    "typical pre-Instagram-filter era phone camera, "
    "slightly muddy colors, reduced dynamic range. "
)


# Structured map of degradation prompts with metadata
# Each prompt has an ID, category, name, description, and the actual prompt text
DEGRADATION_PROMPTS_MAP = {
    # Backlighting issues (2 variations) - HIGH PERFORMERS
    'backlight_1': {
        'name': 'Strong Backlight',
        'description': 'Underexposed subject with blown out background and lens flare',
        'prompt': "Apply strong backlight causing underexposed subject, blown out background, hazy lens flare, auto-exposure failure, silhouette effect partially corrected",
        'category': 'Backlighting'
    },
    'backlight_2': {
        'name': 'Window Backlight',
        'description': 'Harsh window backlight with dark subject and blown out windows',
        'prompt': "Apply harsh window backlight with subject too dark, completely blown out white windows, muddy shadowed face, failed auto-exposure, amateur mistake",
        'category': 'Backlighting'
    },

    # Flash problems (2 variations) - GOOD PERFORMERS
    'flash_1': {
        'name': 'Direct Flash',
        'description': 'On-camera flash with harsh shadows and flat depth',
        'prompt': "Apply direct on-camera flash, harsh shadows behind subject, overexposed foreground, flat depth, artificial lighting",
        'category': 'Flash Problems'
    },
    'flash_2': {
        'name': 'Flash with Red-Eye',
        'description': 'Harsh flash causing red-eye effect and washed out skin',
        'prompt': "Apply harsh flash with red-eye effect, washed out skin tones, sharp shadows, flat lighting, overexposed center",
        'category': 'Flash Problems'
    },

    # Overexposure issues (2 variations) - TOP PERFORMERS
    'overexposure_1': {
        'name': 'Blown Highlights',
        'description': 'Overexposure with blown highlights and lost detail',
        'prompt': "Apply overexposure with blown highlights on face and bright areas, lost detail, harsh bright spots, washed out appearance",
        'category': 'Overexposure'
    },
    'overexposure_2': {
        'name': 'Webcam Quality',
        'description': 'Cheap webcam with overexposed center and noise',
        'prompt': "Apply cheap webcam quality: overexposed center, auto-gain boost creating noise, washed out flat look, artificial oversaturation in patches, low quality sensor",
        'category': 'Overexposure'
    },

    # Low light / underexposure (2 variations) - KEPT FOR VARIETY
    'lowlight_1': {
        'name': 'Dim Ambient Light',
        'description': 'Underexposed shadows with heavy grain from high ISO',
        'prompt': "Apply dim ambient lighting, underexposed shadows, heavy grain from high ISO, slight motion blur, muted colors, poor dynamic range",
        'category': 'Low Light'
    },
    'lowlight_2': {
        'name': 'Poor Indoor Lighting',
        'description': 'Visible noise in dark areas with muddy colors',
        'prompt': "Apply poor indoor lighting, visible noise in dark areas, muddy colors, soft focus from low shutter speed, uneven exposure",
        'category': 'Low Light'
    },

    # Old/cheap camera quality (3 variations) - GOOD PERFORMERS
    'oldcamera_1': {
        'name': 'Old Smartphone',
        'description': 'Old smartphone with compression artifacts and noise',
        'prompt': "Apply old smartphone camera quality: heavy compression artifacts, noise in shadows, poor white balance, soft focus, muddy colors, natural sensor noise",
        'category': 'Old Camera Quality'
    },
    'oldcamera_2': {
        'name': 'Poorly Timed Shot',
        'description': 'Caught mid-blink or unflattering angle',
        'prompt': "Apply poorly timed snapshot: caught mid-blink or mid-expression, awkward unflattering angle, accidental bad timing, candid caught-off-guard look",
        'category': 'Old Camera Quality'
    },
    'oldcamera_3': {
        'name': 'Dirty Lens',
        'description': 'Fingerprint smudge causing blur and haze',
        'prompt': "Apply dirty lens or fingerprint smudge: slight blur in parts, reduced contrast, hazy softness from smudged camera lens, uneven sharpness, casual neglected phone camera",
        'category': 'Old Camera Quality'
    },

    # Out of focus / blur issues (1 variation) - KEPT FOR VARIETY
    'blur_1': {
        'name': 'Motion Blur',
        'description': 'Low shutter speed blur with smeared edges',
        'prompt': "Apply low shutter speed blur: subject and camera both moved, double blur, smeared edges, motion streaks across face, shaky unstable shot",
        'category': 'Focus Issues'
    },

    # Bad white balance (1 variation) - KEPT FOR VARIETY
    'whitebalance_1': {
        'name': 'Orange Color Cast',
        'description': 'Incorrect white balance with strong orange tones',
        'prompt': "Apply incorrect white balance with strong orange color cast, oversaturated warm tones, unnatural skin color, tungsten lighting look",
        'category': 'White Balance'
    }
}

# Legacy array for backward compatibility (if needed elsewhere)
# Dynamically generated from DEGRADATION_PROMPTS_MAP
SPECIFIC_DEGRADATION_PROMPTS = [prompt_data['prompt'] for prompt_data in DEGRADATION_PROMPTS_MAP.values()]


def get_enabled_degradation_prompts() -> list[str]:
    """
    Get only enabled degradation prompts from Config settings.

    Checks Config database for each prompt's enabled state (degradation_<prompt_id>).
    If a prompt is not in the database, it defaults to enabled (True).

    Returns:
        list[str]: List of enabled prompt strings (not including base compression)
    """
    from models import Config  # Import here to avoid circular imports

    enabled_prompts = []
    for prompt_id, prompt_data in DEGRADATION_PROMPTS_MAP.items():
        config_key = f'degradation_{prompt_id}'
        # Default to True (enabled) if not found in database
        if Config.get_value(config_key, default=True):
            enabled_prompts.append(prompt_data['prompt'])

    return enabled_prompts


def get_random_degradation_prompt() -> str:
    """
    Get a random style degradation prompt for Stage 2 image-to-image generation.

    Combines BASE_COMPRESSION_PREFIX (always applied) with a random specific
    degradation issue for variety. Only selects from enabled prompts.

    Returns:
        str: Complete degradation prompt with base compression + specific issue
             If all prompts are disabled, returns base compression only
    """
    enabled_prompts = get_enabled_degradation_prompts()

    # Handle edge case where all prompts are disabled
    if not enabled_prompts:
        logger.warning("All degradation prompts disabled, using base compression only")
        return BASE_COMPRESSION_PREFIX

    specific_issue = random.choice(enabled_prompts)
    full_prompt = BASE_COMPRESSION_PREFIX + specific_issue
    logger.debug(f"Selected degradation: base compression + {specific_issue[:60]}...")
    return full_prompt


def get_degradation_prompt_count() -> int:
    """
    Get the total number of available specific degradation prompts.

    Returns:
        int: Total count of specific degradation prompts (excludes base prefix)
    """
    return len(SPECIFIC_DEGRADATION_PROMPTS)


def get_all_degradation_prompts() -> list[str]:
    """
    Get all FULL degradation prompts (base + each specific issue).

    Returns:
        list[str]: Complete list of all full degradation prompts (base + specific)
    """
    return [BASE_COMPRESSION_PREFIX + specific for specific in SPECIFIC_DEGRADATION_PROMPTS]


# For testing
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print(f"Total degradation prompts: {get_degradation_prompt_count()}")
    print("\n" + "="*80)
    print("Sample of 5 random prompts:")
    print("="*80)

    for i in range(5):
        prompt = get_random_degradation_prompt()
        print(f"\n{i+1}. {prompt}")
