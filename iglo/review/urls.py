from django.urls import path

from review.views import TeacherDetailView, TeacherListView

urlpatterns = [
    path('teachers', TeacherListView.as_view(), name="teacher-list"),
    path('teachers/<first_name>-<last_name>', TeacherDetailView.as_view(), name="teacher-detail"),
]
