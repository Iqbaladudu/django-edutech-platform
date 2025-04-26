from django.contrib import admin
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.utils.html import format_html
from .models import Subject, Course, Module, Content, Text, File, Image, Video

class ModuleInlineFormset(forms.models.BaseInlineFormSet):
    def clean(self):
        super().clean()
        # Validasi bahwa tidak ada modul dengan order sama
        orders = []
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE'):
                order = form.cleaned_data.get('order')
                if order and order in orders:
                    raise forms.ValidationError("Modul tidak dapat memiliki urutan yang sama.")
                orders.append(order)

class ModuleInline(admin.StackedInline):
    model = Module
    formset = ModuleInlineFormset
    extra = 0
    max_num = 50
    fields = ['title', 'description', 'order']
    classes = ['collapse']
    show_change_link = True

class ContentInline(admin.StackedInline):
    model = Content
    extra = 1
    fields = ['content_type', 'object_id', 'order', 'content_preview']
    readonly_fields = ['content_preview']
    classes = ['collapse']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'content_type':
            kwargs['queryset'] = ContentType.objects.filter(
                model__in=('text', 'file', 'image', 'video')
            ).order_by('model')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def content_preview(self, obj):
        if obj.pk and hasattr(obj, 'item') and obj.item:
            return format_html('<div class="content-preview">{}</div>', obj.item.render())
        return "Konten akan tampil setelah disimpan"
    content_preview.short_description = "Preview"

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'course_count']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'owner', 'created', 'updated', 'is_active', 'module_count']
    list_filter = ['created', 'updated', 'subject', 'is_active']
    search_fields = ['title', 'overview']
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['owner', 'subject']
    filter_horizontal = ['students']
    inlines = [ModuleInline]

    fieldsets = (
        ('Informasi Dasar', {
            'fields': ('owner', 'title', 'slug', 'subject')
        }),
        ('Deskripsi', {
            'fields': ('overview',)
        }),
        ('Status dan Pendaftaran', {
            'fields': ('is_active', 'students')
        }),
    )

    def save_formset(self, request, form, formset, change):
        # Set owner untuk modul baru
        if formset.model == Module:
            instances = formset.save(commit=False)
            for instance in instances:
                if not instance.pk:  # Instance baru
                    instance.owner = form.instance.owner
                instance.save()
        else:
            formset.save()

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'content_count']
    list_filter = ['course']
    search_fields = ['title', 'description', 'course__title']
    raw_id_fields = ['course']
    inlines = [ContentInline]

# Register content models
@admin.register(Text)
class TextAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'created', 'updated']
    search_fields = ['title', 'content']

@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'created', 'file_size_display']

    def file_size_display(self, obj):
        if obj.file_size:
            # Display human-readable file size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if obj.file_size < 1024 or unit == 'GB':
                    return f"{obj.file_size:.1f} {unit}"
                obj.file_size /= 1024
        return "-"
    file_size_display.short_description = "Size"

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'created', 'image_preview']

    def image_preview(self, obj):
        if obj.file:
            return format_html('<img src="{}" style="max-height: 50px" />', obj.file.url)
        return "-"
    image_preview.short_description = "Preview"

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'created', 'provider', 'duration_display']

    def duration_display(self, obj):
        if obj.duration:
            minutes, seconds = divmod(obj.duration, 60)
            hours, minutes = divmod(minutes, 60)
            if hours:
                return f"{hours}h {minutes}m"
            return f"{minutes}m {seconds}s"
        return "-"
    duration_display.short_description = "Duration"

# Optional: register Content if you want to manage it directly
@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ['module', 'content_type_display', 'item_title', 'order']
    list_filter = ['module__course']
    search_fields = ['module__title']
    raw_id_fields = ['module']

    def content_type_display(self, obj):
        return obj.content_type.model.capitalize()
    content_type_display.short_description = "Type"

    def item_title(self, obj):
        if hasattr(obj.item, 'title'):
            return obj.item.title
        return "-"
    item_title.short_description = "Title"
