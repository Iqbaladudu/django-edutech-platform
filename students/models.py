from django.db import models
from django.contrib.auth.models import User
from courses.models import Content

class ContentCompletion(models.Model):
    """Model untuk melacak konten yang telah diselesaikan oleh siswa."""
    user = models.ForeignKey(
        User,
        related_name='content_completions',
        on_delete=models.CASCADE
    )
    content = models.ForeignKey(
        Content,
        related_name='completions',
        on_delete=models.CASCADE
    )
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['user', 'content']]
        verbose_name = 'Penyelesaian Konten'
        verbose_name_plural = 'Penyelesaian Konten'
