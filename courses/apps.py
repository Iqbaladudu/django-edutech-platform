from django.apps import AppConfig


class CoursesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField' # type: ignore
    name = 'courses'
    verbose_name = 'Manajemen Kursus'
