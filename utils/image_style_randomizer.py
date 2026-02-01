"""
Image Style Randomization Utility
Applies random post-processing to images to simulate different photographers/sources.

This module provides functions to randomize image characteristics including:
- Color presets (Natural, Warm, Cool, Matte, Punchy, Desaturated)
- Contrast adjustments
- Saturation adjustments
- Sharpness/Blur (Gaussian blur or Unsharp mask)
- Grain/Noise
- Vignette effects
- JPEG compression variation

Target processing time: <500ms per image
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance
from io import BytesIO
import random
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class ColorPreset:
    """Enum-like class for color presets."""
    NATURAL = "natural"
    WARM = "warm"
    COOL = "cool"
    MATTE = "matte"
    PUNCHY = "punchy"
    DESATURATED = "desaturated"

    ALL_PRESETS = [NATURAL, WARM, COOL, MATTE, PUNCHY, DESATURATED]


def randomize_image_style(image_bytes: bytes) -> bytes:
    """
    Apply random style processing to an image to simulate different photographers/sources.

    Processing order:
    1. Color preset (temp shift + saturation)
    2. Contrast adjustment
    3. Blur OR sharpen (50/50 choice)
    4. Grain (60% chance)
    5. Vignette (50% chance)
    6. JPEG compression variation

    Args:
        image_bytes: Input image as bytes (e.g., PNG)

    Returns:
        bytes: Processed image with randomized style as JPEG bytes

    Raises:
        Exception: If image processing fails
    """
    try:
        start_time = cv2.getTickCount()

        # Load image using Pillow for initial processing
        pil_image = Image.open(BytesIO(image_bytes))

        # Convert RGBA to RGB if needed
        if pil_image.mode == 'RGBA':
            # Create white background
            background = Image.new('RGB', pil_image.size, (255, 255, 255))
            background.paste(pil_image, mask=pil_image.split()[3])
            pil_image = background
        elif pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')

        logger.debug(f"Loaded image: {pil_image.size[0]}x{pil_image.size[1]}px, mode={pil_image.mode}")

        # Step 1: Apply random color preset
        preset = random.choice(ColorPreset.ALL_PRESETS)
        pil_image = _apply_color_preset(pil_image, preset)
        logger.debug(f"Applied color preset: {preset}")

        # Step 2: Apply random contrast adjustment (-5% to +15%, bias toward +5 to +12%)
        contrast_factor = random.uniform(0.95, 1.15)
        if random.random() < 0.7:  # 70% chance of positive contrast boost
            contrast_factor = random.uniform(1.05, 1.12)

        enhancer = ImageEnhance.Contrast(pil_image)
        pil_image = enhancer.enhance(contrast_factor)
        logger.debug(f"Applied contrast: {contrast_factor:.2f}x")

        # Convert to numpy array for OpenCV operations
        np_image = np.array(pil_image)

        # Step 3: Apply blur OR sharpen (50/50 choice)
        if random.random() < 0.5:
            # Gaussian blur (0.3-0.7px)
            blur_sigma = random.uniform(0.3, 0.7)
            np_image = cv2.GaussianBlur(np_image, (0, 0), blur_sigma)
            logger.debug(f"Applied Gaussian blur: sigma={blur_sigma:.2f}")
        else:
            # Unsharp mask (sharpening)
            amount = random.uniform(0.4, 0.7)
            np_image = _apply_unsharp_mask(np_image, amount=amount, radius=1.0)
            logger.debug(f"Applied unsharp mask: amount={amount:.2f}")

        # Step 4: Apply grain (60% chance)
        if random.random() < 0.6:
            grain_sigma = random.uniform(3, 8)
            np_image = _add_grain(np_image, sigma=grain_sigma)
            logger.debug(f"Applied grain: sigma={grain_sigma:.1f}")

        # Step 5: Apply vignette (50% chance)
        if random.random() < 0.5:
            vignette_strength = random.uniform(0.12, 0.18)
            np_image = _apply_vignette(np_image, strength=vignette_strength)
            logger.debug(f"Applied vignette: strength={vignette_strength:.2f}")

        # Convert back to PIL for final JPEG compression
        pil_image = Image.fromarray(np_image)

        # Step 6: Apply random JPEG compression (78-95 quality)
        jpeg_quality = random.randint(78, 95)
        output_buffer = BytesIO()
        pil_image.save(output_buffer, format='JPEG', quality=jpeg_quality, optimize=True)
        result_bytes = output_buffer.getvalue()

        # Calculate processing time
        elapsed = (cv2.getTickCount() - start_time) / cv2.getTickFrequency() * 1000
        logger.info(f"Style randomization completed in {elapsed:.1f}ms (JPEG quality={jpeg_quality})")

        return result_bytes

    except Exception as e:
        logger.error(f"Error randomizing image style: {str(e)}", exc_info=True)
        raise


def _apply_color_preset(image: Image.Image, preset: str) -> Image.Image:
    """
    Apply a color preset to the image.

    Args:
        image: PIL Image in RGB mode
        preset: Color preset name from ColorPreset

    Returns:
        PIL Image with color preset applied
    """
    if preset == ColorPreset.NATURAL:
        # Minimal adjustments, slight saturation boost
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.08)

    elif preset == ColorPreset.WARM:
        # Warm tones: increase reds/yellows, boost saturation
        np_img = np.array(image).astype(np.float32)
        # Shift toward warm (increase R, slight increase G)
        np_img[:, :, 0] = np.clip(np_img[:, :, 0] * 1.10, 0, 255)  # Red
        np_img[:, :, 1] = np.clip(np_img[:, :, 1] * 1.05, 0, 255)  # Green
        image = Image.fromarray(np_img.astype(np.uint8))

        # Boost saturation
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.15)

    elif preset == ColorPreset.COOL:
        # Cool tones: increase blues, reduce reds
        np_img = np.array(image).astype(np.float32)
        # Shift toward cool (decrease R, increase B)
        np_img[:, :, 0] = np.clip(np_img[:, :, 0] * 0.93, 0, 255)  # Red
        np_img[:, :, 2] = np.clip(np_img[:, :, 2] * 1.08, 0, 255)  # Blue
        image = Image.fromarray(np_img.astype(np.uint8))

    elif preset == ColorPreset.MATTE:
        # Lifted blacks, desaturated
        # Lift blacks by adjusting levels
        np_img = np.array(image).astype(np.float32)
        # Lift shadows (add offset to darker pixels)
        np_img = np_img * 0.85 + 38  # Scale down and lift
        np_img = np.clip(np_img, 0, 255)
        image = Image.fromarray(np_img.astype(np.uint8))

        # Desaturate
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(0.75)

    elif preset == ColorPreset.PUNCHY:
        # High saturation, increased contrast
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.30)

    elif preset == ColorPreset.DESATURATED:
        # Low saturation, slight contrast boost
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(0.70)

    return image


def _apply_unsharp_mask(image: np.ndarray, amount: float = 0.5, radius: float = 1.0) -> np.ndarray:
    """
    Apply unsharp mask for sharpening.

    Args:
        image: NumPy array (RGB)
        amount: Sharpening strength (0.0-1.0)
        radius: Blur radius for mask

    Returns:
        NumPy array with sharpening applied
    """
    # Create blurred version
    blurred = cv2.GaussianBlur(image, (0, 0), radius)

    # Sharpened = Original + amount * (Original - Blurred)
    sharpened = cv2.addWeighted(image, 1.0 + amount, blurred, -amount, 0)

    return sharpened


def _add_grain(image: np.ndarray, sigma: float = 5.0) -> np.ndarray:
    """
    Add film grain / noise to image.

    Args:
        image: NumPy array (RGB)
        sigma: Noise strength (standard deviation)

    Returns:
        NumPy array with grain applied
    """
    # Generate Gaussian noise
    noise = np.random.normal(0, sigma, image.shape)

    # Add noise to image
    noisy_image = image.astype(np.float32) + noise
    noisy_image = np.clip(noisy_image, 0, 255)

    return noisy_image.astype(np.uint8)


def _apply_vignette(image: np.ndarray, strength: float = 0.15) -> np.ndarray:
    """
    Apply vignette effect (darken corners).

    Args:
        image: NumPy array (RGB)
        strength: Vignette strength (0.0-1.0), how much to darken corners

    Returns:
        NumPy array with vignette applied
    """
    height, width = image.shape[:2]

    # Create radial gradient mask
    # Center point
    center_x, center_y = width / 2, height / 2

    # Create coordinate grids
    Y, X = np.ogrid[:height, :width]

    # Calculate distance from center (normalized)
    max_distance = np.sqrt(center_x**2 + center_y**2)
    distance = np.sqrt((X - center_x)**2 + (Y - center_y)**2) / max_distance

    # Create vignette mask (1.0 at center, darker at edges)
    # Use quadratic falloff for smooth transition
    vignette_mask = 1.0 - (distance**2 * strength)
    vignette_mask = np.clip(vignette_mask, 0, 1)

    # Expand mask to 3 channels
    vignette_mask = np.stack([vignette_mask] * 3, axis=2)

    # Apply vignette
    vignetted = image.astype(np.float32) * vignette_mask
    vignetted = np.clip(vignetted, 0, 255)

    return vignetted.astype(np.uint8)
