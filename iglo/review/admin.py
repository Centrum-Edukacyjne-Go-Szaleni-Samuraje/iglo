from django.contrib import admin

from review.models import Teacher


class TeacherModelAdmin(admin.ModelAdmin):
    pass


admin.site.register(Teacher, TeacherModelAdmin)
