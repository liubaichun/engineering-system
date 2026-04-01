from django.apps import AppConfig


class ApprovalsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'approvals'
    verbose_name = '审批流管理'

    def ready(self):
        # Import signals to register them
        import approvals.signals  # noqa
