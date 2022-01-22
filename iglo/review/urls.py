from django.urls import path

from review.views import TeacherDetailView

urlpatterns = [
    path('teachers/<first_name>-<last_name>', TeacherDetailView.as_view(), name="teacher-detail"),
]
