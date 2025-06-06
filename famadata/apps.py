from django.apps import AppConfig

class FamadataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'famadata'

    # def ready(self):
    #     import alerts.signals  # ✅ correct full import path
