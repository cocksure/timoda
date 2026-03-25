import os
from io import BytesIO
from django.utils.text import slugify
from django.core.files.base import ContentFile
from PIL import Image


def process_image(image, upload_path="uploads/", max_size=(1920, 1080), quality=92, max_file_size_mb=20):
    """
    Processes uploaded image:
    - Checks file size
    - Resizes only if larger than max_size (preserves original resolution otherwise)
    - Converts to WebP at high quality
    - Returns (filename, ContentFile)
    """
    if hasattr(image, 'size') and image.size > max_file_size_mb * 1024 * 1024:
        raise ValueError(f"Файл слишком большой: максимум {max_file_size_mb} МБ")

    img = Image.open(image)

    # Convert RGBA/P/LA to RGB
    if img.mode in ('RGBA', 'LA'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1])
        img = background
    elif img.mode == 'P':
        img = img.convert('RGBA')
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1])
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # Resize only if the image exceeds max_size — never upscale
    if img.width > max_size[0] or img.height > max_size[1]:
        img.thumbnail(max_size, Image.LANCZOS)

    output = BytesIO()
    img.save(output, format="WEBP", quality=quality, method=6)
    output.seek(0)

    filename_wo_ext = os.path.splitext(os.path.basename(image.name))[0]
    safe_name = (slugify(filename_wo_ext) or "image") + ".webp"

    # Return only filename — callers use FieldFile.save() which prepends upload_to
    return safe_name, ContentFile(output.read())


# Max dimensions per context — only downscale if image exceeds these
PRODUCT_IMAGE_MAX  = (1800, 2400)   # high-res product shots (portrait)
CATEGORY_IMAGE_MAX = (900, 900)
BANNER_IMAGE_MAX   = (1920, 1080)
AVATAR_MAX         = (400, 400)