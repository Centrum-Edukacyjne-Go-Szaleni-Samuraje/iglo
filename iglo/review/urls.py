from django.urls import path

from review.views import TeacherDetailView, TeacherListView, ReviewListView

urlpatterns = [
    path('teachers', TeacherListView.as_view(), name="teacher-list"),
    path('teachers/<slug>', TeacherDetailView.as_view(), name="teacher-detail"),
    path('reviews', ReviewListView.as_view(), name="reviews-list")
]
