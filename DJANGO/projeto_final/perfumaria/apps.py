from django.apps import AppConfig


class PerfumariaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'perfumaria'
    
    def ready(self):
        import perfumaria.signals # Importa o arquivo de signals
