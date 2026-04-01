from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Attachment


@receiver(post_save, sender=Attachment)
def generate_thumbnail_on_save(sender, instance, created, **kwargs):
    """附件创建/更新后自动生成缩略图"""
    if not created and not instance.thumbnail:
        # 只在新创建时生成，避免每次保存都重生成
        return

    if instance.file and not instance.thumbnail:
        from .utils import create_thumbnail_for_attachment
        thumb_path = create_thumbnail_for_attachment(instance)
        if thumb_path:
            Attachment.objects.filter(pk=instance.pk).update(thumbnail=thumb_path)
