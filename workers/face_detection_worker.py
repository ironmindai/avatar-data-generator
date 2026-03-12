#!/usr/bin/env python3
"""
Face Detection Worker

This worker processes unanalyzed images in dataset_images table and detects faces.
Designed to run as a cron job every minute with file-based locking to prevent overlapping runs.

Features:
- File-based locking to prevent double-runs
- Batch processing (50 images at a time)
- Graceful error handling
- Comprehensive logging
- Memory-efficient processing

Status Flow:
    face_count IS NULL -> analyze with face_detection_service -> update face_count
                                                                   (0 = no faces, 1+ = faces detected)

Database Schema:
    Table: dataset_images
    Columns: id, dataset_id, image_url, face_count (nullable integer)
    face_count values: NULL = not analyzed, 0 = no faces, 1+ = faces detected

Lock File Location: /tmp/face_detection_worker.lock
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to Python path for imports
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from app import create_app
from models import db, DatasetImage
from services.face_detection_service import detect_faces_in_image_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration
LOCK_FILE = Path("/tmp/face_detection_worker.lock")
BATCH_SIZE = 50
DETECTION_SCORE_THRESHOLD = 0.8
DETECTION_TIMEOUT = 30


class LockManager:
    """
    Manages file-based locking to prevent concurrent worker execution.

    Uses a PID-based lock file to detect stale locks from crashed processes.
    """

    def __init__(self, lock_path: Path):
        """
        Initialize lock manager.

        Args:
            lock_path: Path to lock file
        """
        self.lock_path = lock_path
        self.acquired = False

    def _is_process_running(self, pid: int) -> bool:
        """
        Check if a process with given PID is running.

        Args:
            pid: Process ID to check

        Returns:
            True if process is running, False otherwise
        """
        try:
            # Send signal 0 to check if process exists (doesn't actually send signal)
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def acquire(self) -> bool:
        """
        Attempt to acquire the lock.

        Returns:
            True if lock acquired successfully, False if another process holds the lock
        """
        try:
            # Check if lock file exists
            if self.lock_path.exists():
                # Read PID from lock file
                try:
                    with open(self.lock_path, 'r') as f:
                        old_pid = int(f.read().strip())

                    # Check if process is still running
                    if self._is_process_running(old_pid):
                        logger.info(f"Lock held by running process PID {old_pid} - exiting")
                        return False
                    else:
                        logger.warning(f"Stale lock detected (PID {old_pid} not running) - removing")
                        self.lock_path.unlink()

                except (ValueError, IOError) as e:
                    logger.warning(f"Invalid lock file - removing: {e}")
                    self.lock_path.unlink()

            # Create lock file with current PID
            current_pid = os.getpid()
            with open(self.lock_path, 'w') as f:
                f.write(str(current_pid))

            self.acquired = True
            logger.info(f"Lock acquired (PID {current_pid})")
            return True

        except Exception as e:
            logger.error(f"Error acquiring lock: {e}", exc_info=True)
            return False

    def release(self):
        """Release the lock by removing the lock file."""
        try:
            if self.acquired and self.lock_path.exists():
                self.lock_path.unlink()
                logger.info("Lock released")
                self.acquired = False
        except Exception as e:
            logger.error(f"Error releasing lock: {e}", exc_info=True)

    def __enter__(self):
        """Context manager entry - acquire lock."""
        if not self.acquire():
            raise RuntimeError("Failed to acquire lock")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - release lock."""
        self.release()


class FaceDetectionWorker:
    """
    Face Detection Worker

    Processes unanalyzed images in batches and updates face_count column.
    """

    def __init__(self, batch_size: int = BATCH_SIZE):
        """
        Initialize worker.

        Args:
            batch_size: Number of images to process in one run
        """
        self.batch_size = batch_size
        self.app = create_app()
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0
        self.faces_detected_count = 0

    def get_unanalyzed_images(self, limit: int):
        """
        Fetch unanalyzed images from database.

        Args:
            limit: Maximum number of images to fetch

        Returns:
            List of DatasetImage objects with face_count IS NULL
        """
        try:
            images = DatasetImage.query.filter(
                DatasetImage.face_count.is_(None)
            ).order_by(
                DatasetImage.added_at.asc()
            ).limit(limit).all()

            logger.info(f"Found {len(images)} unanalyzed images (batch size: {limit})")
            return images

        except Exception as e:
            logger.error(f"Error fetching unanalyzed images: {e}", exc_info=True)
            return []

    def process_image(self, image: DatasetImage) -> bool:
        """
        Process a single image and update face_count.

        Args:
            image: DatasetImage object to process

        Returns:
            True if processing succeeded, False if failed
        """
        try:
            logger.debug(f"Processing image ID {image.id}: {image.image_url}")

            # Detect faces
            face_count = detect_faces_in_image_url(
                image.image_url,
                score_threshold=DETECTION_SCORE_THRESHOLD,
                timeout=DETECTION_TIMEOUT
            )

            # Handle detection result
            if face_count is None:
                # Detection failed - skip this image (leave face_count as NULL)
                logger.warning(f"Face detection failed for image ID {image.id} - skipping")
                return False

            # Update face_count
            image.face_count = face_count
            db.session.commit()

            # Log result
            if face_count == 0:
                logger.info(f"Image ID {image.id}: NO faces detected")
            else:
                logger.info(f"Image ID {image.id}: {face_count} face(s) detected")
                self.faces_detected_count += face_count

            return True

        except Exception as e:
            logger.error(f"Error processing image ID {image.id}: {e}", exc_info=True)
            db.session.rollback()
            return False

    def run(self):
        """
        Main worker execution.

        Fetches unanalyzed images and processes them in batches.
        """
        start_time = time.time()
        logger.info("=" * 80)
        logger.info("Face Detection Worker started")
        logger.info(f"Batch size: {self.batch_size}")
        logger.info(f"Score threshold: {DETECTION_SCORE_THRESHOLD}")
        logger.info(f"Detection timeout: {DETECTION_TIMEOUT}s")
        logger.info("=" * 80)

        with self.app.app_context():
            try:
                # Fetch unanalyzed images
                images = self.get_unanalyzed_images(self.batch_size)

                if not images:
                    logger.info("No unanalyzed images found - nothing to do")
                    return

                # Process each image
                for image in images:
                    self.processed_count += 1

                    success = self.process_image(image)

                    if success:
                        self.success_count += 1
                    else:
                        self.error_count += 1

                # Summary
                duration = time.time() - start_time
                logger.info("=" * 80)
                logger.info("Face Detection Worker completed")
                logger.info(f"Images processed: {self.processed_count}")
                logger.info(f"Successful: {self.success_count}")
                logger.info(f"Failed/Skipped: {self.error_count}")
                logger.info(f"Total faces detected: {self.faces_detected_count}")
                logger.info(f"Duration: {duration:.2f} seconds")
                logger.info("=" * 80)

            except Exception as e:
                logger.error(f"Worker execution failed: {e}", exc_info=True)
                raise


def main():
    """Main entry point for worker."""
    try:
        # Attempt to acquire lock
        lock = LockManager(LOCK_FILE)

        if not lock.acquire():
            # Another instance is running - exit silently
            sys.exit(0)

        try:
            # Run worker
            worker = FaceDetectionWorker(batch_size=BATCH_SIZE)
            worker.run()

        finally:
            # Always release lock
            lock.release()

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


def process_face_detection_batch(batch_size: int = 50) -> int:
    """
    Process face detection for a batch of unanalyzed images.

    Simplified version for APScheduler integration (no locking needed).
    Queries DatasetImage records where face_count is None (unanalyzed),
    processes up to batch_size images, and updates the face_count field.

    Args:
        batch_size: Maximum number of images to process in this batch (default: 50)

    Returns:
        Number of images successfully processed

    Example:
        >>> processed_count = process_face_detection_batch(batch_size=50)
        >>> print(f"Processed {processed_count} images")

    Notes:
        - face_count=0+ indicates successful detection (0 means no faces found)
        - face_count=-1 indicates detection error (network, decode, etc.)
        - Logs progress every 10 images
        - Commits after processing all images in batch
        - All exceptions are caught and logged, never crashes
        - Designed for use with APScheduler (no file locking)
    """
    try:
        # Query unanalyzed images (face_count is None)
        unanalyzed_images = DatasetImage.query.filter_by(face_count=None).limit(batch_size).all()

        if not unanalyzed_images:
            # No work to do - return silently to avoid log spam
            return 0

        total_images = len(unanalyzed_images)
        logger.info(f"[FACE_DETECTION] Starting batch processing: {total_images} unanalyzed images")

        processed_count = 0
        error_count = 0

        for idx, image in enumerate(unanalyzed_images, start=1):
            try:
                # Detect faces in image
                face_count = detect_faces_in_image_url(
                    image.image_url,
                    score_threshold=DETECTION_SCORE_THRESHOLD,
                    timeout=DETECTION_TIMEOUT
                )

                if face_count is not None:
                    # Success - update face_count (0+ faces detected)
                    image.face_count = face_count
                    processed_count += 1
                else:
                    # Error - mark as error with -1
                    image.face_count = -1
                    error_count += 1
                    logger.warning(f"[FACE_DETECTION] Failed to detect faces for image {image.id} ({image.image_url})")

                # Log progress every 10 images
                if idx % 10 == 0:
                    logger.info(f"[FACE_DETECTION] Progress: {idx}/{total_images} images processed")

            except Exception as e:
                # Handle unexpected errors gracefully
                logger.error(f"[FACE_DETECTION] Error processing image {image.id}: {e}", exc_info=True)
                image.face_count = -1  # Mark as error
                error_count += 1

        # Commit all changes in a single transaction
        db.session.commit()

        logger.info(
            f"[FACE_DETECTION] Batch completed: {processed_count} successful, "
            f"{error_count} errors, {total_images} total"
        )

        return processed_count

    except Exception as e:
        # Handle database or query errors
        logger.error(f"[FACE_DETECTION] Fatal error in batch processing: {e}", exc_info=True)
        db.session.rollback()
        return 0


if __name__ == '__main__':
    main()
