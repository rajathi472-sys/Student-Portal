from django.urls import path
from . import views
from . import api_views
from .api_views import (
    TeacherDeleteAPIView, StudentDeleteAPIView,
    FeesDeleteAPIView, CGPADeleteAPIView,
    TeacherUpdateAPIView, TeacherDetailAPIView,
    StudentDetailAPIView, StudentUpdateAPIView,
     ManagementLoginAPIView, ManagementCreateAPIView,
    AdminLoginAPIView, AdminCreateAPIView,
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

# Management
   # path('admin-panel/management/',               views.admin_create_management,  name='admin_create_management'),
    #path('admin-panel/management/<int:mgmt_id>/delete/', views.admin_delete_management, name='admin_delete_management'),
    # ── Create endpoints ─────────────────────────────────────────
    path('api/teacher/create/',           api_views.TeacherCreateAPIView.as_view(),    name='api_teacher_create'),
    path('api/student/create/',           api_views.StudentCreateAPIView.as_view(),    name='api_student_create'),
    path('api/fees/create/',              api_views.FeesCreateAPIView.as_view(),       name='api_fees_create'),
    path('api/cgpa/create/',              api_views.CGPACreateAPIView.as_view(),       name='api_cgpa_create'),

    # ── Auth endpoints ───────────────────────────────────────────
    path('api/student/login/',            api_views.StudentLoginAPIView.as_view(),     name='api_student_login'),
    path('api/teacher/login/',            api_views.TeacherLoginAPIView.as_view(),     name='api_teacher_login'),
    path('api/logout/',                   api_views.LogoutAPIView.as_view(),           name='api_logout'),

    # ── Teacher endpoints ────────────────────────────────────────
    path('api/teacher/student/<int:id>/', api_views.TeacherStudentAPIView.as_view(),   name='api_teacher_student'),
    path('api/teacher/<int:id>/',         TeacherDetailAPIView.as_view(),              name='api_teacher_detail'),
    path('api/teacher/<int:id>/update/',  TeacherUpdateAPIView.as_view(),              name='api_teacher_update'),
    path('api/teacher/<str:id>/delete/',  TeacherDeleteAPIView.as_view(),              name='api_teacher_delete'),

    # ── Student endpoints ────────────────────────────────────────
    path('api/student/<int:id>/',         StudentDetailAPIView.as_view(),              name='api_student_detail'),
    path('api/student/<int:id>/update/',  StudentUpdateAPIView.as_view(),              name='api_student_update'),
    path('api/student/<int:id>/delete/',  StudentDeleteAPIView.as_view(),              name='api_student_delete'),

    # ── Fees & CGPA endpoints ────────────────────────────────────
    path('api/fees/<int:id>/delete/',     FeesDeleteAPIView.as_view(),                 name='api_fees_delete'),
    path('api/cgpa/<int:id>/delete/',     CGPADeleteAPIView.as_view(),                 name='api_cgpa_delete'),

    # ── Admin endpoints ──────────────────────────────────────────
    path('api/admin/create/',             AdminCreateAPIView.as_view(),                name='api_admin_create'),
    path('api/admin/login/',              AdminLoginAPIView.as_view(),                 name='api_admin_login'),

    # ── Management endpoints ─────────────────────────────────────
    path('api/management/create/',        ManagementCreateAPIView.as_view(),           name='api_management_create'),
    path('api/management/login/',         ManagementLoginAPIView.as_view(),            name='api_management_login'),

    
]