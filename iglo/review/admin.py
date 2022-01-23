from django.contrib import admin

from review.models import Teacher


class TeacherModelAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("first_name", "last_name")}


admin.site.register(Teacher, TeacherModelAdmin)
