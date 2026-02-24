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
    "blocky compression in flat areas, typical pre-Instagram-filter era phone camera, "
    "slightly muddy colors, reduced dynamic range. PLUS: "
)


# Diverse collection of specific degradation issues
# ONE of these is randomly selected and added to the base compression
SPECIFIC_DEGRADATION_PROMPTS = [
    # Backlighting issues (2 variations)
    "Apply strong backlight causing underexposed subject, blown out background, hazy lens flare, auto-exposure failure, silhouette effect partially corrected",
    "Apply harsh window backlight with subject too dark, completely blown out white windows, muddy shadowed face, failed auto-exposure, amateur mistake",

    # Flash problems (2 variations)
    "Apply direct on-camera flash, harsh shadows behind subject, overexposed foreground, flat depth, artificial lighting",
    "Apply harsh flash with red-eye effect, washed out skin tones, sharp shadows, flat lighting, overexposed center",

    # Low light / underexposure (3 variations)
    "Apply dim ambient lighting, underexposed shadows, heavy grain from high ISO, slight motion blur, muted colors, poor dynamic range",
    "Apply poor indoor lighting, visible noise in dark areas, muddy colors, soft focus from low shutter speed, uneven exposure",
    "Apply evening indoor lighting, high ISO grain throughout, slight blur, warm yellow color cast, compressed shadows",

    # Harsh overhead lighting (2 variations)
    "Apply harsh overhead fluorescent lighting with greenish tint, unflattering shadows under eyes and chin, washed out colors, institutional look",
    "Apply bright overhead office lighting, flat top-down shadows, pale washed out skin, sterile fluorescent color cast",

    # Old/cheap camera quality (3 variations)
    "Apply old smartphone camera quality: heavy compression artifacts, noise in shadows, poor white balance, soft focus, muddy colors, natural sensor noise",
    "Apply poorly timed snapshot: caught mid-blink or mid-expression, awkward unflattering angle, accidental bad timing, candid caught-off-guard look",
    "Apply dirty lens or fingerprint smudge: slight blur in parts, reduced contrast, hazy softness from smudged camera lens, uneven sharpness, casual neglected phone camera",

    # Out of focus / blur issues (1 variation)
    "Apply low shutter speed blur: subject and camera both moved, double blur, smeared edges, motion streaks across face, shaky unstable shot",

    # Bad white balance / color issues (2 variations)
    "Apply incorrect white balance with strong orange color cast, oversaturated warm tones, unnatural skin color, tungsten lighting look",
    "Apply cool blue color cast from bad auto white balance, desaturated look, cold fluorescent feel, unnatural tones",

    # Overexposure issues (2 variations)
    "Apply overexposure with blown highlights on face and bright areas, lost detail, harsh bright spots, washed out appearance",
    "Apply cheap webcam quality: overexposed center, auto-gain boost creating noise, washed out flat look, artificial oversaturation in patches, low quality sensor",
]


def get_random_degradation_prompt() -> str:
    """
    Get a random style degradation prompt for Stage 2 image-to-image generation.

    Combines BASE_COMPRESSION_PREFIX (always applied) with a random specific
    degradation issue for variety.

    Returns:
        str: Complete degradation prompt with base compression + specific issue
    """
    specific_issue = random.choice(SPECIFIC_DEGRADATION_PROMPTS)
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
