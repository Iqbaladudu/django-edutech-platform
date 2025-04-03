from typing import List, Union, Any

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.text import slugify

from .fields import OrderField


class Subject(models.Model):
    """Kategori mata pelajaran yang tersedia dalam platform."""
    title = models.CharField(max_length=200, help_text="Judul mata pelajaran")
    slug = models.SlugField(max_length=200, unique=True, help_text="URL-friendly judul")

    class Meta:
        ordering = ['title']
        indexes = [
            models.Index(fields=['slug']),  # Optimasi pencarian berdasarkan slug
        ]
        verbose_name = "Mata Pelajaran"
        verbose_name_plural = "Mata Pelajaran"

    def __str__(self) -> str:
        return self.title

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Auto-generate slug from title jika belum ada."""
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        """Generate URL untuk detail mata pelajaran."""
        return reverse('subject_detail', args=[self.slug])

    @property
    def course_count(self) -> int:
        """Jumlah kursus dalam mata pelajaran ini."""
        return self.courses.count() # type: ignore


class Course(models.Model):
    """Kursus yang dapat diikuti oleh pengguna."""
    owner = models.ForeignKey(
        User,
        related_name='courses_created',
        on_delete=models.CASCADE,
        help_text="Instruktur yang membuat kursus"
    )
    subject = models.ForeignKey(
        Subject,
        related_name='courses',
        on_delete=models.CASCADE,
        help_text="Mata pelajaran yang berkaitan dengan kursus"
    )
    students = models.ManyToManyField(  # Nama field diperbaiki dari 'student' -> 'students'
        User,
        related_name='courses_joined',
        blank=True,
        help_text="Siswa yang terdaftar dalam kursus"
    )
    title = models.CharField(max_length=200, help_text="Judul kursus")
    slug = models.SlugField(max_length=200, unique=True, help_text="URL-friendly judul")
    overview = models.TextField(help_text="Deskripsi singkat tentang kursus")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)  # Tambahan untuk tracking perubahan
    is_active = models.BooleanField(default=True, help_text="Status kursus aktif atau tidak") # type: ignore

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['-created']),
            models.Index(fields=['is_active']),
        ]
        verbose_name = "Kursus"
        verbose_name_plural = "Kursus"

    def __str__(self) -> str:
        return self.title

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Auto-generate slug from title jika belum ada."""
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        """Generate URL untuk detail kursus."""
        return reverse('course_detail', args=[self.slug])

    @property
    def module_count(self) -> int:
        """Jumlah modul dalam kursus ini."""
        return self.modules.count() # type: ignore

    @property
    def student_count(self) -> int:
        """Jumlah siswa yang terdaftar dalam kursus."""
        return self.students.count() # type: ignore

    @property
    def total_duration(self) -> int:
        """Total durasi kursus dalam menit."""
        # Implementasi sesuai kebutuhan
        return 0  # Default


class Module(models.Model):
    """Modul pembelajaran dalam kursus."""
    course = models.ForeignKey(
        Course,
        related_name='modules',
        on_delete=models.CASCADE,
        help_text="Kursus yang memiliki modul ini"
    )
    title = models.CharField(max_length=200, help_text="Judul modul")
    description = models.TextField(blank=True, help_text="Deskripsi tentang modul")
    order = OrderField(blank=True, for_fields=['course'], help_text="Urutan modul dalam kursus")

    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['order']),
        ]
        verbose_name = "Modul"
        verbose_name_plural = "Modul"

    def __str__(self) -> str:
        return f'{self.order}. {self.title}'

    def get_absolute_url(self) -> str:
        """Generate URL untuk detail modul."""
        return reverse('module_detail', args=[self.course.slug, self.order]) # type: ignore

    @property
    def content_count(self) -> int:
        """Jumlah konten dalam modul ini."""
        return self.contents.count() # type: ignore


class ItemBase(models.Model):
    """Model abstrak untuk berbagai jenis konten pembelajaran."""
    owner = models.ForeignKey(
        User,
        related_name='%(class)s_related',
        on_delete=models.CASCADE,
        help_text="Pembuat konten ini"
    )
    title = models.CharField(max_length=200, help_text="Judul konten")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['-created']),
        ]

    def __str__(self) -> str:
        return self.title # type: ignore

    def render(self) -> str:
        """Render template HTML untuk jenis konten ini."""
        return render_to_string(
            f'courses/content/{self._meta.model_name}.html', # type: ignore
            {'item': self}
        )

    def get_content_type(self) -> str:
        """Mendapatkan nama tipe konten."""
        return self._meta.model_name # type: ignore


class Text(ItemBase):
    """Konten berupa teks."""
    content = models.TextField(help_text="Isi teks")

    class Meta(ItemBase.Meta):
        verbose_name = "Konten Teks"
        verbose_name_plural = "Konten Teks"


class File(ItemBase):
    """Konten berupa file."""
    file = models.FileField(
        upload_to='files',
        help_text="Upload file (PDF, DOC, XLS, dll)"
    )
    file_size = models.PositiveIntegerField(
        editable=False,
        null=True,
        help_text="Ukuran file dalam bytes"
    )

    class Meta(ItemBase.Meta):
        verbose_name = "File"
        verbose_name_plural = "File"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Simpan ukuran file saat file diupload."""
        if self.file:
            self.file_size = self.file.size # type: ignore
        super().save(*args, **kwargs)


class Image(ItemBase):
    """Konten berupa gambar."""
    file = models.ImageField(  # Mengganti FileField dengan ImageField
        upload_to='images',
        help_text="Upload gambar (JPG, PNG, GIF)"
    )
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        help_text="Teks alternatif untuk aksesibilitas"
    )

    class Meta(ItemBase.Meta):
        verbose_name = "Gambar"
        verbose_name_plural = "Gambar"


class Video(ItemBase):
    """Konten berupa video."""
    class VideoProvider(models.TextChoices):
        YOUTUBE = 'YT', 'YouTube'
        VIMEO = 'VM', 'Vimeo'
        OTHER = 'OT', 'Other'

    url = models.URLField(help_text="URL video (YouTube, Vimeo, dll)")
    provider = models.CharField(
        max_length=2,
        choices=VideoProvider.choices,
        default=VideoProvider.YOUTUBE,
        help_text="Penyedia layanan video"
    )
    duration = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Durasi video dalam detik"
    )

    class Meta(ItemBase.Meta):
        verbose_name = "Video"
        verbose_name_plural = "Video"

    def get_embed_code(self) -> str:
        """Mendapatkan kode embed untuk video."""
        # Implementasi sesuai kebutuhan berdasarkan provider
        return f'<iframe src="{self.url}" frameborder="0" allowfullscreen></iframe>'


class Content(models.Model):
    """Hubungan antara modul dan konten berbagai jenis."""
    module = models.ForeignKey(
        Module,
        related_name='contents',
        on_delete=models.CASCADE,
        help_text="Modul yang memiliki konten ini"
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={'model__in': ('text', 'video', 'image', 'file')},
        help_text="Jenis konten"
    )
    object_id = models.PositiveIntegerField(help_text="ID objek konten")
    item = GenericForeignKey('content_type', 'object_id')
    order = OrderField(
        blank=True,
        for_fields=['module'],
        help_text="Urutan konten dalam modul"
    )

    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['order']),
        ]
        verbose_name = "Konten"
        verbose_name_plural = "Konten"

    def __str__(self) -> str:
        return f"{self.module.title} - {self.item.title} ({self.get_item_type_display()})" # type: ignore

    def get_item_type_display(self) -> str:
        """Mendapatkan nama tipe konten yang mudah dibaca."""
        return self.content_type.model.capitalize()

    @staticmethod
    def get_contents_for_module(module_id: int) -> List:
        """
        Mendapatkan semua konten untuk modul tertentu dengan prefetch objek terkait.
        Mengoptimalkan query dengan mengurangi N+1 problem.
        """
        return Content.objects.filter(module_id=module_id).select_related( # type: ignore
            'content_type'
        ).prefetch_related(
            'item'
        ).order_by('order')
