from django.apps import AppConfig


class PharmacyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pharmacy"

    def ready(self):
        import pharmacy.signals  # Import the signals
