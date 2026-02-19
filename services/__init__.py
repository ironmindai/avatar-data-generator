"""
Services package for Avatar Data Generator.
Contains service modules for external API integrations.
"""

from .flowise_service import generate_image_prompt
from .image_generation import generate_base_image
from .image_prompt_chain import get_prompt_chain
from .seedream_service import generate_image_with_reference, generate_images_batch as generate_seedream_batch
from .image_utils import upload_to_s3, upload_images_batch, generate_presigned_url

# Deprecated (replaced by SeeDream workflow):
# from .image_generation import generate_images_from_base
# from .image_utils import split_and_trim_image

__all__ = [
    'generate_image_prompt',
    'generate_base_image',
    'get_prompt_chain',
    'generate_image_with_reference',
    'generate_seedream_batch',
    'upload_to_s3',
    'upload_images_batch',
    'generate_presigned_url'
]
