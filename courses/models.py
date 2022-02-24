from django.db.models import Model
from django.contrib.auth.models import User
from django.db.models import CharField, SlugField, TextField, DateTimeField, PositiveIntegerField, FileField, URLField, CASCADE, ForeignKey, ManyToManyField
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from .fields import OrderField
from django.template.loader import render_to_string

class Subject(Model):
    title = CharField(max_length=200)
    slug = SlugField(max_length=200, unique=True)
    class Meta:
        ordering = ['title']
    def __str__(self):
        return self.title

class Course(Model):
    owner = ForeignKey(User,
    related_name='courses_created', on_delete=CASCADE)
    subject = ForeignKey(Subject, related_name='courses', on_delete=CASCADE)
    student = ManyToManyField(User, related_name='courses_joined', blank=True)
    title = CharField(max_length=200)
    slug = SlugField(max_length=200, unique=True)
    overview = TextField()
    created = DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created']
    def __str__(self):
        return self.title

class Module(Model):
    course = ForeignKey(Course, related_name='modules', on_delete=CASCADE)
    title = CharField(max_length=200)
    description = TextField(blank=True)
    order = OrderField(blank=True, for_fields=['course'])
    class Meta:
        ordering = ['order']
    def __str__(self):
        return f'{self.order}. {self.title}'

class ItemBase(Model):
    owner = ForeignKey(User,
    related_name='%(class)s_related', on_delete=CASCADE)
    title = CharField(max_length=200)
    created = DateTimeField(auto_now_add=True)
    updated = DateTimeField(auto_now=True)
    class Meta:
        abstract = True
    def __str__(self):
        return self.title
    def render(self):
        return render_to_string(f'courses/content/{self._meta.model_name}.html', {'item': self})

class Text(ItemBase):
    content = TextField()
class File(ItemBase):
    file = FileField(upload_to='files')
class Image(ItemBase):
    file = FileField(upload_to='images')
class Video(ItemBase):
    url = URLField()

class Content(Model):
    module = ForeignKey(Module, related_name='contents', on_delete=CASCADE)
    content_type = ForeignKey(ContentType, on_delete=CASCADE, limit_choices_to={'model__in':('text', 'video', 'image', 'file')})
    object_id = PositiveIntegerField()
    item = GenericForeignKey('content_type', 'object_id')
    order = OrderField(blank=True, for_fields=['module'])
    class Meta:
        ordering = ['order']