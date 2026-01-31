"""
Image Cropping Utility
Provides white border removal functionality for generated images.

This module contains the border removal logic extracted from playground
experiments and integrated into the main application for production use.
"""

from PIL import Image
from io import BytesIO
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def remove_white_borders(
    image_bytes: bytes,
    threshold: int = 230,
    edge_scan_depth: int = 50,
    min_border_width: int = 5
) -> bytes:
    """
    Remove white borders from an image.

    Detects and removes white/light-colored borders from images on any edges.
    Uses Pillow to scan edges and crop to content boundaries.

    Args:
        image_bytes: Image data as bytes (e.g., PNG)
        threshold: Pixel values above this are considered white (0-255).
                   Default 230 is more aggressive than 240.
        edge_scan_depth: How many pixels deep to scan from each edge (default: 50)
        min_border_width: Minimum consecutive white pixels to consider a border (default: 5)

    Returns:
        bytes: Cropped image as PNG bytes. If no borders detected or error occurs,
               returns original image bytes.

    Raises:
        Exception: If image processing fails
    """
    try:
        # Load image from bytes
        image = Image.open(BytesIO(image_bytes))
        original_size = image.size

        logger.debug(f"Processing image for border removal: {original_size[0]}x{original_size[1]}px")

        # Detect borders on all edges
        borders = _detect_all_borders(image, threshold, edge_scan_depth, min_border_width)

        # Check if any borders were detected
        total_border = sum(borders.values())
        if total_border == 0:
            logger.debug("No white borders detected, returning original image")
            return image_bytes

        logger.debug(f"Detected borders: top={borders['top']}px, bottom={borders['bottom']}px, "
                    f"left={borders['left']}px, right={borders['right']}px")

        # Calculate crop boundaries
        width, height = image.size
        left = borders['left']
        top = borders['top']
        right = width - borders['right']
        bottom = height - borders['bottom']

        # Validate boundaries
        if top >= bottom or left >= right:
            logger.warning("Invalid crop boundaries detected, returning original image")
            return image_bytes

        # Crop image
        cropped = image.crop((left, top, right, bottom))
        cropped_size = cropped.size

        # Calculate reduction stats
        removed_w = original_size[0] - cropped_size[0]
        removed_h = original_size[1] - cropped_size[1]
        logger.info(f"Cropped white borders: removed {removed_w}x{removed_h}px, "
                   f"final size {cropped_size[0]}x{cropped_size[1]}px")

        # Convert back to bytes
        output_buffer = BytesIO()
        cropped.save(output_buffer, format='PNG')
        return output_buffer.getvalue()

    except Exception as e:
        logger.error(f"Error removing white borders: {str(e)}", exc_info=True)
        logger.warning("Returning original image due to error")
        return image_bytes


def _detect_all_borders(
    image: Image.Image,
    threshold: int,
    edge_scan_depth: int,
    min_border_width: int
) -> dict:
    """
    Detect white borders on all edges of an image.

    Args:
        image: PIL Image object
        threshold: White threshold (0-255)
        edge_scan_depth: Scan depth in pixels
        min_border_width: Minimum border width to consider

    Returns:
        dict: Border widths for each edge {'top': px, 'bottom': px, 'left': px, 'right': px}
    """
    borders = {
        'top': _detect_border_top(image, threshold, edge_scan_depth, min_border_width),
        'bottom': _detect_border_bottom(image, threshold, edge_scan_depth, min_border_width),
        'left': _detect_border_left(image, threshold, edge_scan_depth, min_border_width),
        'right': _detect_border_right(image, threshold, edge_scan_depth, min_border_width)
    }
    return borders


def _is_white_row(pixels, y: int, width: int, height: int, threshold: int) -> bool:
    """Check if a row is predominantly white (95% or more white pixels)."""
    white_count = 0
    for x in range(width):
        pixel = pixels[x, y]
        if isinstance(pixel, tuple):
            # RGB/RGBA - check all channels
            if all(c >= threshold for c in pixel[:3]):
                white_count += 1
        else:
            # Grayscale
            if pixel >= threshold:
                white_count += 1

    return white_count >= width * 0.95


def _is_white_column(pixels, x: int, width: int, height: int, threshold: int) -> bool:
    """Check if a column is predominantly white (95% or more white pixels)."""
    white_count = 0
    for y in range(height):
        pixel = pixels[x, y]
        if isinstance(pixel, tuple):
            # RGB/RGBA - check all channels
            if all(c >= threshold for c in pixel[:3]):
                white_count += 1
        else:
            # Grayscale
            if pixel >= threshold:
                white_count += 1

    return white_count >= height * 0.95


def _detect_border_top(
    image: Image.Image,
    threshold: int,
    edge_scan_depth: int,
    min_border_width: int
) -> int:
    """Detect white border on top edge."""
    width, height = image.size
    pixels = image.load()
    scan_depth = min(edge_scan_depth, height)

    for y in range(scan_depth):
        if not _is_white_row(pixels, y, width, height, threshold):
            return y if y >= min_border_width else 0

    return 0


def _detect_border_bottom(
    image: Image.Image,
    threshold: int,
    edge_scan_depth: int,
    min_border_width: int
) -> int:
    """Detect white border on bottom edge."""
    width, height = image.size
    pixels = image.load()
    scan_depth = min(edge_scan_depth, height)

    for y in range(height - 1, height - scan_depth - 1, -1):
        if not _is_white_row(pixels, y, width, height, threshold):
            border_width = height - y - 1
            return border_width if border_width >= min_border_width else 0

    return 0


def _detect_border_left(
    image: Image.Image,
    threshold: int,
    edge_scan_depth: int,
    min_border_width: int
) -> int:
    """Detect white border on left edge."""
    width, height = image.size
    pixels = image.load()
    scan_depth = min(edge_scan_depth, width)

    for x in range(scan_depth):
        if not _is_white_column(pixels, x, width, height, threshold):
            return x if x >= min_border_width else 0

    return 0


def _detect_border_right(
    image: Image.Image,
    threshold: int,
    edge_scan_depth: int,
    min_border_width: int
) -> int:
    """Detect white border on right edge."""
    width, height = image.size
    pixels = image.load()
    scan_depth = min(edge_scan_depth, width)

    for x in range(width - 1, width - scan_depth - 1, -1):
        if not _is_white_column(pixels, x, width, height, threshold):
            border_width = width - x - 1
            return border_width if border_width >= min_border_width else 0

    return 0
