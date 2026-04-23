from django.urls import path
from . import views
from . import api_views
from .api_views import (
    StudentLoginAPI, ManagementLoginAPI, LogoutAPI,
)

urlpatterns = [

    # ── Template-based views ────────────────────────────────────
    path('',                              views.home,                          name='home'),
    path('student/login/',                views.student_login,                 name='student_login'),
    path('student/dashboard/',            views.student_dashboard,             name='student_dashboard'),
    path('student/cgpa/',                 views.view_cgpa,                     name='view_cgpa'),
    path('student/fees/',                 views.view_fees,                     name='view_fees'),
    path('teacher/login/',                views.teacher_login,                 name='teacher_login'),
    path('teacher/dashboard/',            views.teacher_dashboard,             name='teacher_dashboard'),
    path('teacher/edit/<int:id>/',        views.teacher_edit_student,          name='teacher_edit_student'),
    path('logout/',                       views.logout_view,                   name='logout'),
    path('management-login/',             views.management_login,              name='management_login'),
    path('management/dashboard/',         views.management_dashboard,          name='management_dashboard'),
    path('management/reminders/',         views.trigger_reminders,             name='trigger_reminders'),
    path('management/student/<int:student_id>/fees/', views.management_student_fees_detail, name='management_student_fees_detail'),
    # ── Add these URL patterns to your accounts/urls.py ─────────────

    #path('admin-panel/login/',                    views.admin_login,              name='admin_login'),
    #path('admin-panel/dashboard/',                views.admin_dashboard,          name='admin_dashboard'),

# Students
    #path('admin-panel/students/',                 views.admin_students,           name='admin_students'),
    #path('admin-panel/students/<int:student_id>/edit/',   views.admin_edit_student,   name='admin_edit_student'),
    #path('admin-panel/students/<int:student_id>/delete/', views.admin_delete_student, name='admin_delete_student'),

# Teachers
    #path('admin-panel/teachers/',                 views.admin_teachers,           name='admin_teachers'),
    #path('admin-panel/teachers/<int:teacher_id>/edit/',   views.admin_edit_teacher,   name='admin_edit_teacher'),
    #path('admin-panel/teachers/<int:teacher_id>/delete/', views.admin_delete_teacher, name='admin_delete_teacher'),

# Fees
    #path('admin-panel/fees/',                     views.admin_fees,               name='admin_fees'),
# MANAGEMENT — STUDENT CRUD
    path('management/students/',                   views.management_students,       name='management_students'),
    path('management/students/add/',               views.management_add_student,    name='management_add_student'),
    path('management/students/edit/<int:id>/',     views.management_edit_student,   name='management_edit_student'),
    path('management/students/delete/<int:id>/',   views.management_delete_student, name='management_delete_student'),

    # MANAGEMENT — TEACHER CRUD
    path('management/teachers/',                   views.management_teachers,       name='management_teachers'),
    path('management/teachers/add/',               views.management_add_teacher,    name='management_add_teacher'),
    path('management/teachers/edit/<int:id>/',     views.management_edit_teacher,   name='management_edit_teacher'),
    path('management/teachers/delete/<int:id>/',   views.management_delete_teacher, name='management_delete_teacher'),

# ── Auth endpoints ───────────────────────────────────────────
    path('api/student/login/',            api_views.StudentLoginAPI.as_view(),         name='api_student_login'),
    path('api/management/login/',         api_views.ManagementLoginAPI.as_view(),      name='api_management_login'),
    path('api/logout/',                   api_views.LogoutAPI.as_view(),               name='api_logout'),

    # ── Student endpoints ────────────────────────────────────────
    path('api/student/profile/',          api_views.StudentProfileAPI.as_view(),       name='api_student_profile'),
    path('api/student/cgpa/',             api_views.StudentCGPAAPI.as_view(),          name='api_student_cgpa'),
    path('api/student/fees/',             api_views.StudentFeesAPI.as_view(),          name='api_student_fees'),

    # ── Management endpoints ─────────────────────────────────────
    path('api/management/dashboard/',     api_views.ManagementDashboardAPI.as_view(),  name='api_management_dashboard'),
    path('api/management/students/',      api_views.ManagementStudentListAPI.as_view(),         name='api_management_students'),
    path('api/management/students/<int:id>/',    api_views.ManagementStudentDetailAPI.as_view(), name='api_management_student_detail'),
    path('api/management/students/<int:student_id>/fees/', api_views.ManagementStudentFeesAPI.as_view(), name='api_management_student_fees'),
    path('api/management/reminders/',     api_views.ManagementTriggerRemindersAPI.as_view(),     name='api_management_reminders'),
    
]