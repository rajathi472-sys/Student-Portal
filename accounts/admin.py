
from django.contrib import admin
from .models import Student, Teacher, Fees, CGPA, Admin,Management

admin.site.register(Student)
admin.site.register(Teacher)
#admin.site.register(Admin)
admin.site.register(Fees)
admin.site.register(CGPA)
admin.site.register(Management)