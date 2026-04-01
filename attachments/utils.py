import os
from PIL import Image
from django.conf import settings


def generate_thumbnail(source_path, target_path, size=(200, 200)):
    """生成缩略图"""
    try:
        img = Image.open(source_path)
        img.thumbnail(size, Image.Resampling.LANCZOS)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        img.save(target_path, quality=85, optimize=True)
        return True
    except Exception as e:
        print(f"[Thumbnail] Failed: {e}")
        return False


def create_thumbnail_for_attachment(attachment):
    """为附件生成缩略图"""
    if not attachment or not attachment.file:
        return None

    ext = os.path.splitext(attachment.file.name)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        return None  # 非图片不生成缩略图

    # 缩略图路径: attachments/thumbnails/thumb_<原文件名>
    thumb_name = f"thumb_{os.path.basename(attachment.file.name)}"
    thumb_dir = os.path.join(settings.MEDIA_ROOT, 'attachments', 'thumbnails')
    os.makedirs(thumb_dir, exist_ok=True)
    thumb_path = os.path.join(thumb_dir, thumb_name)
    thumb_relative = f"attachments/thumbnails/{thumb_name}"

    source_path = attachment.file.path

    if generate_thumbnail(source_path, thumb_path):
        return thumb_relative
    return None
