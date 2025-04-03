import os
import django
import random
from django.utils.text import slugify
from faker import Faker
import io
from django.core.files.base import ContentFile

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

# Import models
from django.contrib.auth.models import User
from courses.models import Subject, Course, Module, Text, File, Image, Video, Content
from django.contrib.contenttypes.models import ContentType
fake = Faker('id_ID')

def run():
    # Create admin user
    if not User.objects.filter(username='iqbaladudu').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin')
        print("Admin user created: admin/admin")

    # Create regular users
    for i in range(50):
        first_name = fake.first_name()
        last_name = fake.last_name()
        username = f"{first_name.lower()}{random.randint(1, 999)}"

        try:
            User.objects.create_user(
                username=username,
                email=fake.email(),
                password='password123',
                first_name=first_name,
                last_name=last_name
            )
        except:
            pass

    print(f"Created {User.objects.count()} users")

    # Create subjects
    subjects = []
    for i in range(10):
        title = fake.unique.bs()
        slug = slugify(title)

        subject, created = Subject.objects.get_or_create(
            title=title,
            slug=slug
        )
        subjects.append(subject)

    print(f"Created {len(subjects)} subjects")

    # Create courses
    instructors = list(User.objects.all()[:5])
    courses = []

    for i in range(30):
        title = fake.unique.catch_phrase()
        slug = slugify(title)

        course = Course.objects.create(
            owner=random.choice(instructors),
            subject=random.choice(subjects),
            title=title,
            slug=slug,
            overview=fake.paragraph(),
            is_active=random.choice([True, True, True, False])
        )

        # Add students
        students = random.sample(
            list(User.objects.all()),
            random.randint(0, 15)
        )
        course.students.add(*students)
        courses.append(course)

    print(f"Created {len(courses)} courses")

    # Create modules and content
    for course in courses:
        module_count = random.randint(3, 8)

        for m in range(module_count):
            module = Module.objects.create(
                course=course,
                title=fake.sentence(),
                description=fake.paragraph()
            )

            content_count = random.randint(3, 10)

            for c in range(content_count):
                content_type = random.choice(['text', 'file', 'image', 'video'])

                if content_type == 'text':
                    item = Text.objects.create(
                        owner=course.owner,
                        title=fake.sentence(),
                        content='\n\n'.join(fake.paragraphs(nb=3))
                    )
                elif content_type == 'file':
                    dummy_content = ContentFile(b"Ini adalah file dummy untuk testing")
                    item = File.objects.create(
                            owner=course.owner,
                            title=fake.sentence(),
                            # File sebenarnya akan dibuat
                            file_size=len(dummy_content.file.getvalue())
                        )
                    # Simpan file secara terpisah (untuk menghindari validasi saat create)
                    item.file.save('dummy.pdf', dummy_content, save=True)
                elif content_type == 'image':
                    # Buat gambar dummy (1x1 pixel transparan PNG)
                    dummy_image = ContentFile(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')
                    item = Image.objects.create(
                            owner=course.owner,
                            title=fake.sentence(),
                            alt_text=fake.sentence()
                        )
                    item.file.save('dummy.jpg', dummy_image, save=True)
                elif content_type == 'video':
                    platforms = ['YT', 'VM', 'OT']
                    urls = {
                        'YT': 'https://www.youtube.com/embed/dQw4w9WgXcQ',
                        'VM': 'https://player.vimeo.com/video/148751763',
                        'OT': 'https://example.com/video/12345'
                    }

                    platform = random.choice(platforms)
                    item = Video.objects.create(
                        owner=course.owner,
                        title=fake.sentence(),
                        url=urls[platform],
                        provider=platform,
                        duration=random.randint(60, 3600)
                    )

                # Create content
                content_type_obj = ContentType.objects.get_for_model(item)
                Content.objects.create(
                    module=module,
                    content_type=content_type_obj,
                    object_id=item.id
                )

    print("Created modules and content for all courses")
    print("Database population complete!")

if __name__ == '__main__':
    run()
