"""
Image Set Service - Scene Image Selection and Usage Tracking

This module provides production-ready functions for managing scene image selection
from image datasets during avatar generation tasks.

Key Features:
- Smart image selection prioritizing globally least-used images
- Task-level deduplication to avoid repetition within a task
- Automatic cycling when all images have been used
- Usage tracking for analytics and fairness
"""

import logging
from typing import List, Tuple, Optional
from sqlalchemy import func, and_, exists
from sqlalchemy.exc import IntegrityError

from models import db, DatasetImage, ImageDataset, DatasetImageUsage, GenerationTask

# Configure logging
logger = logging.getLogger(__name__)


def get_next_scene_image(image_set_ids: List[int], task_id: int) -> Tuple[str, int]:
    """
    Get the next scene image URL to use, prioritizing globally least-used images.

    This function implements smart image selection that:
    1. Filters images from the specified image sets
    2. Excludes images already used in THIS specific task (to avoid repetition)
    3. Prioritizes images with the lowest global usage count across all tasks
    4. Uses random tiebreaker for images with equal usage
    5. Automatically cycles by resetting when all images have been used in this task

    Args:
        image_set_ids: List of image dataset IDs to select from
        task_id: The generation task ID (primary key from generation_tasks table)

    Returns:
        Tuple of (image_url, dataset_image_id)

    Raises:
        ValueError: If no images are available in the specified image sets

    Example:
        >>> image_url, image_id = get_next_scene_image([1, 2, 3], 42)
        >>> print(f"Using image {image_id}: {image_url}")
    """
    try:
        # First, try to get images NOT yet used in this specific task
        # Ordered by global usage count (least used first), then random
        unused_image = db.session.query(
            DatasetImage.id,
            DatasetImage.image_url,
            func.count(DatasetImageUsage.id).label('usage_count')
        ).join(
            ImageDataset, DatasetImage.dataset_id == ImageDataset.id
        ).outerjoin(
            DatasetImageUsage, DatasetImage.id == DatasetImageUsage.dataset_image_id
        ).filter(
            ImageDataset.id.in_(image_set_ids)
        ).filter(
            ~DatasetImage.id.in_(
                db.session.query(DatasetImageUsage.dataset_image_id).filter(
                    DatasetImageUsage.task_id == task_id
                )
            )
        ).group_by(
            DatasetImage.id,
            DatasetImage.image_url
        ).order_by(
            func.count(DatasetImageUsage.id).asc(),
            func.random()
        ).first()

        if unused_image:
            logger.info(f"Selected unused image {unused_image.id} for task {task_id} (global usage: {unused_image.usage_count})")
            return (unused_image.image_url, unused_image.id)

        # If all images have been used in this task, cycle restart
        # Select from all images in the sets, prioritizing globally least-used
        logger.info(f"All images used in task {task_id}, cycling to restart")

        any_image = db.session.query(
            DatasetImage.id,
            DatasetImage.image_url,
            func.count(DatasetImageUsage.id).label('usage_count')
        ).join(
            ImageDataset, DatasetImage.dataset_id == ImageDataset.id
        ).outerjoin(
            DatasetImageUsage, DatasetImage.id == DatasetImageUsage.dataset_image_id
        ).filter(
            ImageDataset.id.in_(image_set_ids)
        ).group_by(
            DatasetImage.id,
            DatasetImage.image_url
        ).order_by(
            func.count(DatasetImageUsage.id).asc(),
            func.random()
        ).first()

        if not any_image:
            error_msg = f"No images available in image sets {image_set_ids}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"Cycled to image {any_image.id} for task {task_id} (global usage: {any_image.usage_count})")
        return (any_image.image_url, any_image.id)

    except Exception as e:
        logger.error(f"Error selecting next scene image for task {task_id}: {str(e)}")
        raise


def mark_image_used(dataset_image_id: int, task_id: int, persona_result_id: int) -> None:
    """
    Record that an image was used by a specific persona in a task.

    This function creates a usage record in the dataset_image_usage table,
    which tracks when each image is used by each persona. This enables:
    - Global usage counting across all tasks
    - Persona-level deduplication to avoid repetition within the same persona
    - Allows image reuse across different personas in the same task
    - Analytics on image utilization

    Args:
        dataset_image_id: The dataset image ID (primary key from dataset_images table)
        task_id: The generation task ID (primary key from generation_tasks table)
        persona_result_id: The GenerationResult ID (persona) using this image

    Raises:
        ValueError: If dataset_image_id, task_id, or persona_result_id are invalid

    Example:
        >>> mark_image_used(123, 42, 101)
        # Creates usage record for image 123 used by persona 101 in task 42
    """
    try:
        # Create usage record
        usage_record = DatasetImageUsage(
            dataset_image_id=dataset_image_id,
            task_id=task_id,
            persona_result_id=persona_result_id
        )

        db.session.add(usage_record)
        db.session.commit()

        logger.info(f"Marked image {dataset_image_id} as used by persona {persona_result_id} in task {task_id}")

    except IntegrityError as e:
        # Handle duplicate gracefully (UNIQUE constraint on dataset_image_id + task_id + persona_result_id)
        db.session.rollback()
        logger.warning(f"Image {dataset_image_id} already marked as used by persona {persona_result_id} in task {task_id} (duplicate ignored)")

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error marking image {dataset_image_id} as used by persona {persona_result_id} in task {task_id}: {str(e)}")
        raise


def assign_scene_images_for_persona(image_set_ids: List[int], task_id: int, persona_result_id: int, count: int) -> List[Tuple[str, int]]:
    """
    Pre-assign multiple scene images for a persona, ensuring no duplicates.

    This function selects {count} images with these guarantees:
    1. Prioritizes globally least-used images
    2. Excludes images already used in THIS TASK (task-level deduplication during pre-assignment)
    3. NO duplicates in the returned list
    4. Automatically cycles when all images exhausted
    5. Different personas get different images (maximizes diversity across task)

    NOTE: During pre-assignment phase, we track usage at TASK level to ensure
    different personas get different images. The persona_result_id is still used
    to track which persona owns which image for final database recording.

    Args:
        image_set_ids: List of image dataset IDs to select from
        task_id: The generation task ID
        persona_result_id: The GenerationResult ID (persona) to track final usage
        count: Number of images to assign

    Returns:
        List of (image_url, dataset_image_id) tuples

    Raises:
        ValueError: If no images available in the specified image sets

    Example:
        >>> assigned = assign_scene_images_for_persona([1, 2, 3], 42, 101, 4)
        >>> print(f"Pre-assigned {len(assigned)} scene images")
    """
    try:
        logger.info(f"Pre-assigning {count} scene images for task {task_id} persona {persona_result_id} from image sets {image_set_ids}")

        # First, try to get unused images (NOT yet used in THIS TASK)
        # FIX: Changed from persona-level to task-level deduplication
        # This ensures different personas get different images instead of all drawing from the same pool
        # Ordered by global usage count (least used first), then random
        unused_images = db.session.query(
            DatasetImage.id,
            DatasetImage.image_url,
            func.count(DatasetImageUsage.id).label('usage_count')
        ).join(
            ImageDataset, DatasetImage.dataset_id == ImageDataset.id
        ).outerjoin(
            DatasetImageUsage, DatasetImage.id == DatasetImageUsage.dataset_image_id
        ).filter(
            ImageDataset.id.in_(image_set_ids)
        ).filter(
            ~DatasetImage.id.in_(
                db.session.query(DatasetImageUsage.dataset_image_id).filter(
                    DatasetImageUsage.task_id == task_id
                    # REMOVED: persona_result_id filter - now tracks at task level during pre-assignment
                )
            )
        ).group_by(
            DatasetImage.id,
            DatasetImage.image_url
        ).order_by(
            func.count(DatasetImageUsage.id).asc(),
            func.random()
        ).limit(count).all()

        # Check if we got enough images
        if len(unused_images) >= count:
            result = [(img.image_url, img.id) for img in unused_images]
            logger.info(f"Pre-assigned {len(result)} unused images for task {task_id} persona {persona_result_id} (global usage: {unused_images[0].usage_count} to {unused_images[-1].usage_count})")
            return result

        # If we didn't get enough unused images, we need to cycle
        # Get remaining count from ALL images (including already used in this task)
        remaining_count = count - len(unused_images)
        logger.info(f"Only {len(unused_images)} unused images available in task {task_id}, need {remaining_count} more. Cycling...")

        # Query ALL images, prioritizing globally least-used
        # Exclude the images we already selected above to avoid duplicates
        already_selected_ids = [img.id for img in unused_images]

        additional_images = db.session.query(
            DatasetImage.id,
            DatasetImage.image_url,
            func.count(DatasetImageUsage.id).label('usage_count')
        ).join(
            ImageDataset, DatasetImage.dataset_id == ImageDataset.id
        ).outerjoin(
            DatasetImageUsage, DatasetImage.id == DatasetImageUsage.dataset_image_id
        ).filter(
            ImageDataset.id.in_(image_set_ids)
        ).filter(
            ~DatasetImage.id.in_(already_selected_ids)  # Exclude already selected to prevent duplicates
        ).group_by(
            DatasetImage.id,
            DatasetImage.image_url
        ).order_by(
            func.count(DatasetImageUsage.id).asc(),
            func.random()
        ).limit(remaining_count).all()

        if not additional_images:
            error_msg = f"No additional images available in image sets {image_set_ids} after selecting {len(unused_images)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Combine both sets
        all_selected = list(unused_images) + list(additional_images)
        result = [(img.image_url, img.id) for img in all_selected]

        logger.info(f"Pre-assigned {len(result)} images for task {task_id} persona {persona_result_id} ({len(unused_images)} unused + {len(additional_images)} cycled)")

        # Sanity check: ensure no duplicates
        image_ids = [img_id for _, img_id in result]
        if len(image_ids) != len(set(image_ids)):
            error_msg = f"CRITICAL: Duplicate image IDs detected in pre-assignment: {image_ids}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        return result

    except Exception as e:
        logger.error(f"Error pre-assigning scene images for task {task_id}: {str(e)}")
        raise


def get_usage_count(dataset_image_id: int) -> int:
    """
    Get total usage count for an image across all tasks.

    This function counts how many times a specific image has been used
    across all generation tasks, providing analytics on image utilization.

    Args:
        dataset_image_id: The dataset image ID (primary key from dataset_images table)

    Returns:
        Integer count of how many times this image has been used

    Example:
        >>> count = get_usage_count(123)
        >>> print(f"Image 123 has been used {count} times")
    """
    try:
        usage_count = db.session.query(func.count(DatasetImageUsage.id)).filter(
            DatasetImageUsage.dataset_image_id == dataset_image_id
        ).scalar()

        return usage_count or 0

    except Exception as e:
        logger.error(f"Error getting usage count for image {dataset_image_id}: {str(e)}")
        raise
