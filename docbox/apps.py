from django.apps import AppConfig
from django.db.models.signals import post_save

from docbox.signals.order import update_status


class DocboxConfig(AppConfig):
    name = "docbox"
    verbose_name = "Docbox"

    def ready(self):
        post_save.connect(update_status, sender="docbox.ProviderOrder")
