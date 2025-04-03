from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from courses.models import Subject, Course
from students.forms import CourseEnrollForm

class StudentViewsTest(TestCase):
    """Test untuk view-view di aplikasi students"""

    def setUp(self):
        # Buat client
        self.client = Client()

        # Buat user: satu untuk instruktur, satu lagi untuk student
        self.instructor = User.objects.create_user(
            username='instructor',
            password='instructorpass',
            email='instructor@example.com'
        )

        self.student = User.objects.create_user(
            username='student',
            password='studentpass',
            email='student@example.com'
        )

        # Buat subject
        self.subject = Subject.objects.create(
            title='Test Subject',
            slug='test-subject'
        )

        # Buat beberapa courses
        self.course1 = Course.objects.create(
            owner=self.instructor,
            subject=self.subject,
            title='Course 1',
            slug='course-1',
            overview='This is course 1'
        )

        self.course2 = Course.objects.create(
            owner=self.instructor,
            subject=self.subject,
            title='Course 2',
            slug='course-2',
            overview='This is course 2'
        )

    def test_student_registration(self):
        """Test StudentRegistrationView"""
        # Test GET
        response = self.client.get(reverse('student_registration'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'students/student/registration.html')

        # Test POST
        data = {
            'username': 'newstudent',
            'password1': 'complex-password123',
            'password2': 'complex-password123'
        }

        response = self.client.post(reverse('student_registration'), data)

        # Seharusnya redirect ke student_course_list setelah registrasi berhasil
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('student_course_list'))

        # Verifikasi user baru telah dibuat
        self.assertTrue(User.objects.filter(username='newstudent').exists())

        # Verifikasi user baru sudah login
        response = self.client.get(reverse('student_course_list'))
        self.assertEqual(response.status_code, 200)

    def test_student_enroll_course(self):
        """Test StudentEnrollCourseView"""
        # Login as student
        self.client.login(username='student', password='studentpass')

        # Test enroll
        data = {
            'course': self.course1.id
        }

        response = self.client.post(reverse('student_enroll_course'), data)

        # Seharusnya redirect ke student_course_detail setelah enroll berhasil
        self.assertEqual(response.status_code, 302)

        # Verifikasi student sudah ter-enroll di course
        self.course1.refresh_from_db()
        self.assertIn(self.student, self.course1.students.all())

    def test_student_course_list(self):
        """Test StudentCourseListView"""
        # Login as student
        self.client.login(username='student', password='studentpass')

        # Enroll student ke course1
        self.course1.students.add(self.student)

        # Test view
        response = self.client.get(reverse('student_course_list'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'students/course/list.html')

        # Verifikasi hanya course yang di-enroll yang ditampilkan
        self.assertContains(response, 'Course 1')
        self.assertNotContains(response, 'Course 2')

    def test_student_course_detail(self):
        """Test StudentCourseDetailView"""
        # Login as student
        self.client.login(username='student', password='studentpass')

        # Enroll student ke course1
        self.course1.students.add(self.student)

        # Tambahkan modul ke course1
        module = self.course1.modules.create(
            title='Test Module',
            description='This is a test module'
        )

        # Test view
        response = self.client.get(reverse('student_course_detail', args=[self.course1.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'students/course/detail.html')

        # Verifikasi course dan modul ditampilkan
        self.assertContains(response, 'Course 1')
        self.assertContains(response, 'Test Module')

    def test_student_course_access_restriction(self):
        """Test bahwa student hanya dapat mengakses course yang di-enroll"""
        # Login as student
        self.client.login(username='student', password='studentpass')

        # Buat modul untuk course2 jika belum ada
        if not self.course2.modules.exists():
            self.course2.modules.create(
                title='Module in Course 2',
                description='This is a module in Course 2'
            )

        # Student belum enroll ke course2
        response = self.client.get(reverse('student_course_detail', args=[self.course2.id]))

        # Pengujian pertama: Pastikan tidak bisa mengakses course yang belum di-enroll
        self.assertNotEqual(response.status_code, 200)

        # Sekarang enroll ke course2
        self.course2.students.add(self.student)

        # Coba akses lagi setelah di-enroll
        response = self.client.get(reverse('student_course_detail', args=[self.course2.id]))

        # Seharusnya 200 karena sudah enroll
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Course 2')

class StudentFormsTest(TestCase):
    """Test untuk form-form di aplikasi students"""

    def setUp(self):
        # Buat user
        self.instructor = User.objects.create_user(
            username='instructor',
            password='instructorpass'
        )

        # Buat subject (via foreign key course->subject)
        self.subject = Subject.objects.create(
            title='Test Subject',
            slug='test-subject'
        )

        # Buat course
        self.course = Course.objects.create(
            owner=self.instructor,
            subject=self.subject,
            title='Test Course',
            slug='test-course',
            overview='This is a test course'
        )

    def test_course_enroll_form_valid(self):
        """Test CourseEnrollForm dengan data valid"""
        form_data = {
            'course': self.course.id
        }

        form = CourseEnrollForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['course'], self.course)

    def test_course_enroll_form_hidden_field(self):
        """Test bahwa field course di CourseEnrollForm adalah hidden"""
        form = CourseEnrollForm()
        self.assertEqual(form.fields['course'].widget.__class__.__name__, 'HiddenInput')
