from django.apps import AppConfig


class AttachmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'attachments'
    verbose_name = '附件管理'

    def ready(self):
        import attachments.signals  # noqa
