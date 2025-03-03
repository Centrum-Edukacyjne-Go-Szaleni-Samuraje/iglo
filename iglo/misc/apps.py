from django.apps import AppConfig


class MiscConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'misc'
    
    def ready(self):
        """
        Called when Django starts up, apply profiling to key methods
        """
        # Import and apply profiling in DEBUG mode only
        from django.conf import settings
        if settings.DEBUG:
            # Import here to avoid circular imports
            from misc.profiling import apply_profiling
            apply_profiling()
