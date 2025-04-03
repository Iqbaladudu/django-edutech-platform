from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from django.views.generic.edit import CreateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from courses.models import Course, Content
from .forms import CourseEnrollForm
from django.http import JsonResponse
from .models import ContentCompletion
from django.views import View

class StudentCourseDetailView(DetailView):
    model = Course
    template_name = 'students/course/detail.html'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(students=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # get course object
        course = self.get_object()

        # Load all modules with their contents for efficient access
        modules = list(course.modules.prefetch_related('contents__content_type').order_by('order'))
        all_contents = []

        # Collect all contents from all modules in order
        for module in modules:
            module_contents = list(module.contents.all().order_by('order'))
            for content in module_contents:
                all_contents.append({
                    'module': module,
                    'content': content
                })

        # Initialize variables
        context['modules'] = modules
        context['all_contents'] = all_contents
        context['current_content'] = None
        context['current_module'] = None
        context['previous_content'] = None
        context['next_content'] = None
        context['current_content_index'] = 0
        context['total_contents'] = len(all_contents)

        # Handle content_id parameter if provided
        content_id = self.kwargs.get('content_id')
        if content_id and all_contents:
            # Find the current content and its position
            for index, content_item in enumerate(all_contents):
                if str(content_item['content'].id) == str(content_id):
                    context['current_content'] = content_item['content']
                    context['current_module'] = content_item['module']
                    context['current_content_index'] = index

                    # Set previous content if not the first
                    if index > 0:
                        context['previous_content'] = all_contents[index - 1]['content']

                    # Set next content if not the last
                    if index < len(all_contents) - 1:
                        context['next_content'] = all_contents[index + 1]['content']

                    break
        # If no content_id or couldn't find the content, default to first content
        elif all_contents:
            context['current_content'] = all_contents[0]['content']
            context['current_module'] = all_contents[0]['module']

            # If there's more than one content, set next_content
            if len(all_contents) > 1:
                context['next_content'] = all_contents[1]['content']

        # Calculate progress percentage
        if context['total_contents'] > 0:
            context['progress_percentage'] = int((context['current_content_index'] / context['total_contents']) * 100)
        else:
            context['progress_percentage'] = 0

        return context


class StudentCourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'students/course/list.html'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(students__in=[self.request.user])


class StudentEnrollCourseView(LoginRequiredMixin, FormView):
    course = None
    form_class = CourseEnrollForm

    def form_valid(self, form):
        self.course = form.cleaned_data['course']
        self.course.students.add(self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('student_course_detail', args=[self.course.id])


class StudentRegistrationView(CreateView):
    template_name = 'students/student/registration.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('student_course_list')

    def form_valid(self, form):
        result = super().form_valid(form)
        cd = form.cleaned_data
        user = authenticate(username=cd['username'], password=cd['password1'])
        login(self.request, user)
        return result

class ContentCompletionView(LoginRequiredMixin, View):
    """View untuk menandai konten sebagai selesai."""

    def post(self, request):
        content_id = request.POST.get('content_id')
        if not content_id:
            return JsonResponse({'status': 'error', 'message': 'Content ID is required'}, status=400)

        try:
            content = Content.objects.get(id=content_id)

            # Cek apakah pengguna terdaftar pada kursus ini
            if request.user not in content.module.course.students.all():
                return JsonResponse(
                    {'status': 'error', 'message': 'You are not enrolled in this course'},
                    status=403
                )

            # Buat atau dapatkan catatan penyelesaian
            completion, created = ContentCompletion.objects.get_or_create(
                user=request.user,
                content=content
            )

            if not created:
                # Jika sudah ada, perbarui waktu
                completion.save()  # Auto mengupdate completed_at

            # Hitung progress
            total_contents = Content.objects.filter(module__course=content.module.course).count()
            completed_contents = ContentCompletion.objects.filter(
                user=request.user,
                content__module__course=content.module.course
            ).count()

            progress = int((completed_contents / total_contents) * 100) if total_contents > 0 else 0

            return JsonResponse({
                'status': 'success',
                'message': 'Content marked as complete',
                'progress': progress,
                'completed_at': completion.completed_at.strftime('%Y-%m-%d %H:%M:%S')
            })

        except Content.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Content not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
