from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from .models import Subject, Course, Module, Content, Text, File, Video, Image


class ModelTests(TestCase):
    """Test untuk model-model di aplikasi courses"""

    def setUp(self):
        # Buat user untuk testing
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword',
            email='test@example.com'
        )

        # Buat subject
        self.subject = Subject.objects.create(
            title='Test Subject',
            slug='test-subject'
        )

        # Buat course
        self.course = Course.objects.create(
            owner=self.user,
            subject=self.subject,
            title='Test Course',
            slug='test-course',
            overview='This is a test course'
        )

        # Buat module
        self.module = Module.objects.create(
            course=self.course,
            title='Test Module',
            description='This is a test module'
        )

        # Buat konten text
        self.text = Text.objects.create(
            owner=self.user,
            title='Test Text Content',
            content='This is test text content'
        )

        # Buat content yang menghubungkan module dengan text
        content_type = ContentType.objects.get_for_model(Text)
        self.content = Content.objects.create(
            module=self.module,
            content_type=content_type,
            object_id=self.text.id
        )

    def test_subject_creation(self):
        """Test pembuatan Subject"""
        self.assertEqual(self.subject.title, 'Test Subject')
        self.assertEqual(self.subject.slug, 'test-subject')
        self.assertEqual(str(self.subject), 'Test Subject')

    def test_course_creation(self):
        """Test pembuatan Course"""
        self.assertEqual(self.course.owner, self.user)
        self.assertEqual(self.course.subject, self.subject)
        self.assertEqual(self.course.title, 'Test Course')
        self.assertEqual(self.course.slug, 'test-course')
        self.assertEqual(self.course.overview, 'This is a test course')
        self.assertTrue(self.course.is_active)
        self.assertEqual(str(self.course), 'Test Course')

    def test_module_creation(self):
        """Test pembuatan Module"""
        self.assertEqual(self.module.course, self.course)
        self.assertEqual(self.module.title, 'Test Module')
        self.assertEqual(self.module.description, 'This is a test module')
        self.assertEqual(self.module.order, 0)  # OrderField dimulai dari 0
        # Sesuaikan string format jika __str__ menggunakan nomor order
        # Lihat implementasi __str__ di model Module
        formatted_string = f'0. {self.module.title}'
        self.assertEqual(str(self.module), formatted_string)

    def test_text_content_creation(self):
        """Test pembuatan Text content"""
        self.assertEqual(self.text.owner, self.user)
        self.assertEqual(self.text.title, 'Test Text Content')
        self.assertEqual(self.text.content, 'This is test text content')
        self.assertEqual(str(self.text), 'Test Text Content')

    def test_content_creation(self):
        """Test pembuatan Content"""
        self.assertEqual(self.content.module, self.module)
        self.assertEqual(self.content.item, self.text)
        self.assertEqual(self.content.order, 0)  # OrderField dimulai dari 0

    def test_course_student_relationship(self):
        """Test relasi many-to-many antara Course dan Student"""
        student1 = User.objects.create_user(username='student1', password='password')
        student2 = User.objects.create_user(username='student2', password='password')

        # Tambahkan student ke course
        self.course.students.add(student1, student2)

        # Verifikasi
        self.assertEqual(self.course.students.count(), 2)
        self.assertIn(student1, self.course.students.all())
        self.assertIn(student2, self.course.students.all())

        # Verifikasi dari sisi student
        self.assertIn(self.course, student1.courses_joined.all())
        self.assertIn(self.course, student2.courses_joined.all())

    def test_module_count(self):
        """Test property module_count di Course"""
        # Tambahkan modul baru ke course yang sama
        Module.objects.create(
            course=self.course,
            title='Another Module',
            description='This is another test module'
        )

        self.assertEqual(self.course.module_count, 2)

    def test_content_count(self):
        """Test property content_count di Module"""
        # Tambahkan content baru ke module yang sama
        video = Video.objects.create(
            owner=self.user,
            title='Test Video',
            url='https://youtube.com/watch?v=test',
            provider='YT'
        )

        content_type = ContentType.objects.get_for_model(Video)
        Content.objects.create(
            module=self.module,
            content_type=content_type,
            object_id=video.id
        )

        self.assertEqual(self.module.content_count, 2)

    def test_auto_slug_generation(self):
        """Test auto-generation slug jika tidak diberikan"""
        course = Course.objects.create(
            owner=self.user,
            subject=self.subject,
            title='Auto Slug Test',
            overview='This is a test for auto slug generation'
        )

        self.assertEqual(course.slug, 'auto-slug-test')


class ViewTests(TestCase):
    """Test untuk view-view di aplikasi courses"""

    def setUp(self):
        # Buat client
        self.client = Client()

        # Buat user superuser
        self.user = User.objects.create_superuser(
            username='testadmin',
            password='testpassword',
            email='test@example.com'
        )

        # Buat subject
        self.subject = Subject.objects.create(
            title='Test Subject',
            slug='test-subject'
        )

        # Buat course
        self.course = Course.objects.create(
            owner=self.user,
            subject=self.subject,
            title='Test Course',
            slug='test-course',
            overview='This is a test course'
        )

        # Login
        self.client.login(username='testadmin', password='testpassword')

    def test_course_list_view(self):
        """Test CourseListView"""
        response = self.client.get(reverse('course_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Course')
        self.assertTemplateUsed(response, 'courses/course/list.html')

    def test_course_detail_view(self):
        """Test CourseDetailView"""
        response = self.client.get(reverse('course_detail', args=['test-course']))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Course')
        self.assertContains(response, 'This is a test course')
        self.assertTemplateUsed(response, 'courses/course/detail.html')

    def test_course_list_by_subject(self):
        """Test CourseListView dengan filter by subject"""
        response = self.client.get(reverse('course_list_subject', args=['test-subject']))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Course')
        self.assertTemplateUsed(response, 'courses/course/list.html')

    def test_manage_course_list_view(self):
        """Test ManageCourseListView"""
        response = self.client.get(reverse('manage_course_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Course')
        self.assertTemplateUsed(response, 'courses/manage/course/list.html')

    def test_course_create_view(self):
        """Test CourseCreateView"""
        response = self.client.get(reverse('course_create'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courses/manage/course/form.html')

        # Test post
        data = {
            'title': 'New Test Course',
            'subject': self.subject.id,
            'overview': 'This is a new test course',
            'slug': 'new-test-course'  # Tambahkan slug jika diperlukan
        }

        response = self.client.post(reverse('course_create'), data)

        # Seharusnya redirect ke manage_course_list setelah create berhasil
        self.assertEqual(response.status_code, 302)

        # Verifikasi course baru telah dibuat
        self.assertTrue(Course.objects.filter(title='New Test Course').exists())

    def test_course_update_view(self):
        """Test CourseUpdateView"""
        response = self.client.get(reverse('course_edit', args=[self.course.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courses/manage/course/form.html')

        # Test post
        data = {
            'title': 'Updated Test Course',
            'subject': self.subject.id,
            'overview': 'This is an updated test course',
            'slug': 'updated-test-course'  # Tambahkan slug jika diperlukan
        }

        response = self.client.post(reverse('course_edit', args=[self.course.id]), data)

        # Seharusnya redirect ke manage_course_list setelah update berhasil
        self.assertEqual(response.status_code, 302)

        # Reload course dari database
        self.course.refresh_from_db()

        # Verifikasi course telah diupdate
        self.assertEqual(self.course.title, 'Updated Test Course')
        self.assertEqual(self.course.overview, 'This is an updated test course')

    def test_course_delete_view(self):
        """Test CourseDeleteView"""
        response = self.client.get(reverse('course_delete', args=[self.course.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courses/manage/course/delete.html')

        # Test post
        response = self.client.post(reverse('course_delete', args=[self.course.id]))

        # Seharusnya redirect ke manage_course_list setelah delete berhasil
        self.assertEqual(response.status_code, 302)

        # Verifikasi course telah dihapus
        self.assertFalse(Course.objects.filter(id=self.course.id).exists())
