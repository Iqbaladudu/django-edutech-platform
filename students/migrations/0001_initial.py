# Generated by Django 5.2 on 2025-04-03 12:44

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('courses', '0007_auto_20250403_0857'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ContentCompletion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('completed_at', models.DateTimeField(auto_now_add=True)),
                ('content', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='completions', to='courses.content')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='content_completions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Penyelesaian Konten',
                'verbose_name_plural': 'Penyelesaian Konten',
                'unique_together': {('user', 'content')},
            },
        ),
    ]
