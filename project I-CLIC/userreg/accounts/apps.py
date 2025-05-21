from django.apps import AppConfig
from django.apps import AppConfig
import threading

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

class ScraperConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scraper'

    def ready(self):
        from task import scheduler
        t = threading.Thread(target=scheduler, daemon=True)
        t.start()