from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import BasePermission
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from django.contrib.auth.hashers import check_password
from django.core.mail import send_mail
from django.conf import settings

from .models import Student, Fees, CGPA, Teacher, Management
from .serializers import (
    StudentSerializer, FeesSerializer, CGPASerializer,
    TeacherSerializer, ReceiptSubmitSerializer,
    StudentLoginSerializer, ManagementLoginSerializer,
)


GRADE_POINTS = {
    'O': 10, 'A+': 9, 'A': 8,
    'B+': 7, 'B': 6, 'C': 5, 'F': 0,
}


# ─────────────────────────────────────────────
#  CUSTOM PERMISSIONS
# ─────────────────────────────────────────────

class IsStudentSession(BasePermission):
    def has_permission(self, request, view):
        return bool(request.session.get('roll_no'))


class IsManagementSession(BasePermission):
    def has_permission(self, request, view):
        return bool(request.session.get('management_id'))


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def get_student_from_session(request):
    roll_no = request.session.get('roll_no')
    if not roll_no:
        return None
    try:
        return Student.objects.get(roll_no=roll_no)
    except Student.DoesNotExist:
        return None


def get_management_from_session(request):
    management_id = request.session.get('management_id')
    if not management_id:
        return None
    try:
        return Management.objects.get(management_id=management_id)
    except Management.DoesNotExist:
        return None


def compute_cgpa(cgpa_qs):
    """Returns (semesters_dict, overall_cgpa) for a CGPA queryset."""
    total_credits = sum(GRADE_POINTS.get(c.grade, 0) * c.credits for c in cgpa_qs)
    total_units   = sum(c.credits for c in cgpa_qs)
    overall       = round(total_credits / total_units, 2) if total_units > 0 else 0

    semesters = {}
    for c in cgpa_qs:
        sem = c.semester
        if sem not in semesters:
            semesters[sem] = {'subjects': [], 'credits': 0, 'points': 0}
        semesters[sem]['subjects'].append(CGPASerializer(c).data)
        semesters[sem]['credits'] += c.credits
        semesters[sem]['points']  += GRADE_POINTS.get(c.grade, 0) * c.credits

    for sem in semesters:
        creds = semesters[sem]['credits']
        semesters[sem]['cgpa'] = round(
            semesters[sem]['points'] / creds, 2
        ) if creds > 0 else 0

    return semesters, overall


# ═════════════════════════════════════════════
#  AUTH ENDPOINTS
# ═════════════════════════════════════════════

class StudentLoginAPI(APIView):
    """
    POST /api/student/login/
    Body: { "roll_no": "...", "password": "..." }
    """
    def post(self, request):
        serializer = StudentLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        roll_no  = serializer.validated_data['roll_no']
        password = serializer.validated_data['password']

        try:
            student = Student.objects.get(roll_no=roll_no)
        except Student.DoesNotExist:
            return Response({'error': 'Invalid roll number.'}, status=status.HTTP_401_UNAUTHORIZED)

        if not check_password(password, student.password):
            return Response({'error': 'Invalid password.'}, status=status.HTTP_401_UNAUTHORIZED)

        request.session['roll_no'] = roll_no
        return Response({
            'message': 'Login successful.',
            'student': StudentSerializer(student).data,
        })


class ManagementLoginAPI(APIView):
    """
    POST /api/management/login/
    Body: { "management_id": "...", "password": "..." }
    """
    def post(self, request):
        serializer = ManagementLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        management_id = serializer.validated_data['management_id']
        password      = serializer.validated_data['password']

        try:
            management = Management.objects.get(management_id=management_id)
        except Management.DoesNotExist:
            return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

        if not check_password(password, management.password):
            return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

        request.session['management_id'] = management_id
        return Response({
            'message':       'Login successful.',
            'management_id': management_id,
        })


class LogoutAPI(APIView):
    """
    POST /api/logout/
    Clears the current session regardless of role.
    """
    def post(self, request):
        request.session.flush()
        return Response({'message': 'Logged out successfully.'})


# ═════════════════════════════════════════════
#  STUDENT ENDPOINTS
# ═════════════════════════════════════════════

class StudentProfileAPI(APIView):
    """
    GET /api/student/profile/
    Returns the logged-in student's profile details.
    """
    permission_classes = [IsStudentSession]

    def get(self, request):
        student = get_student_from_session(request)
        return Response(StudentSerializer(student).data)


class StudentCGPAAPI(APIView):
    """
    GET /api/student/cgpa/
    Returns semester-wise CGPA breakdown and overall CGPA.
    """
    permission_classes = [IsStudentSession]

    def get(self, request):
        student            = get_student_from_session(request)
        cgpa_qs            = CGPA.objects.filter(student=student)
        semesters, overall = compute_cgpa(cgpa_qs)
        return Response({
            'overall_cgpa': overall,
            'semesters':    semesters,
        })


class StudentFeesAPI(APIView):
    """
    GET  /api/student/fees/   — View fee details.
    POST /api/student/fees/   — Submit payment receipt.
         Multipart fields: payment_ref, payment_date, receipt_image (file)
    """
    permission_classes = [IsStudentSession]
    parser_classes     = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        student = get_student_from_session(request)
        fees    = Fees.objects.filter(student=student).first()

        if not fees:
            return Response({'fees': None})

        return Response(FeesSerializer(fees, context={'request': request}).data)

    def post(self, request):
        student = get_student_from_session(request)
        fees    = Fees.objects.filter(student=student).first()

        if not fees:
            return Response({'error': 'No fee record found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ReceiptSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        fees.payment_ref    = serializer.validated_data['payment_ref']
        fees.payment_date   = serializer.validated_data['payment_date']
        fees.receipt_image  = serializer.validated_data['receipt_image']
        fees.payment_status = 'pending'
        fees.save()

        return Response({'message': 'Receipt submitted. Awaiting verification.'})


# ═════════════════════════════════════════════
#  MANAGEMENT — DASHBOARD
# ═════════════════════════════════════════════

class ManagementDashboardAPI(APIView):
    """
    GET /api/management/dashboard/
    Returns summary stats and per-student fee overview.
    """
    permission_classes = [IsManagementSession]

    def get(self, request):
        students     = Student.objects.select_related('teacher').all().order_by('name')
        student_data = []

        for student in students:
            fees = Fees.objects.filter(student=student).first()
            student_data.append({
                'student': StudentSerializer(student).data,
                'fees':    FeesSerializer(fees, context={'request': request}).data if fees else None,
            })

        return Response({
            'total_students': students.count(),
            'teacher_count':  Teacher.objects.count(),
            'pending_count':  Fees.objects.filter(payment_status='pending').count(),
            'paid_count':     Fees.objects.filter(payment_status='paid').count(),
            'unpaid_count':   Fees.objects.filter(payment_status='unpaid').count(),
            'students':       student_data,
        })


# ═════════════════════════════════════════════
#  MANAGEMENT — STUDENTS CRUD
# ═════════════════════════════════════════════

class ManagementStudentListAPI(APIView):
    """
    GET  /api/management/students/   — List all students.
    POST /api/management/students/   — Add a new student.
    """
    permission_classes = [IsManagementSession]

    def get(self, request):
        students = Student.objects.select_related('teacher').all().order_by('roll_no')
        return Response({'students': StudentSerializer(students, many=True).data})

    def post(self, request):
        serializer = StudentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        student = serializer.save()
        Fees.objects.create(
            student=student, total_fees=0,
            paid_amount=0, payment_status='unpaid',
        )
        return Response(
            {'message': f'Student {student.name} added successfully.',
             'student': StudentSerializer(student).data},
            status=status.HTTP_201_CREATED,
        )


class ManagementStudentDetailAPI(APIView):
    """
    GET    /api/management/students/<id>/   — Retrieve student.
    PUT    /api/management/students/<id>/   — Update student.
    DELETE /api/management/students/<id>/   — Delete student.
    """
    permission_classes = [IsManagementSession]

    def _get_student(self, id):
        try:
            return Student.objects.get(id=id), None
        except Student.DoesNotExist:
            return None, Response({'error': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)

    def get(self, request, id):
        student, err = self._get_student(id)
        if err:
            return err
        return Response(StudentSerializer(student).data)

    def put(self, request, id):
        student, err = self._get_student(id)
        if err:
            return err

        # partial=True so password is not required on every update
        serializer = StudentSerializer(student, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        student = serializer.save()
        return Response({
            'message': f'Student {student.name} updated successfully.',
            'student': StudentSerializer(student).data,
        })

    def delete(self, request, id):
        student, err = self._get_student(id)
        if err:
            return err
        name = student.name
        student.delete()
        return Response({'message': f'Student {name} deleted successfully.'})


# ═════════════════════════════════════════════
#  MANAGEMENT — FEES
# ═════════════════════════════════════════════

class ManagementStudentFeesAPI(APIView):
    """
    GET  /api/management/students/<student_id>/fees/
    POST /api/management/students/<student_id>/fees/
         actions: set_fees | update_fees | approve | reject
    """
    permission_classes = [IsManagementSession]

    def _get_student(self, student_id):
        try:
            return Student.objects.get(id=student_id), None
        except Student.DoesNotExist:
            return None, Response({'error': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)

    def get(self, request, student_id):
        student, err = self._get_student(student_id)
        if err:
            return err

        fees = Fees.objects.filter(student=student).first()
        if not fees:
            return Response({'fees': None})

        return Response(FeesSerializer(fees, context={'request': request}).data)

    def post(self, request, student_id):
        student, err = self._get_student(student_id)
        if err:
            return err

        fees   = Fees.objects.filter(student=student).first()
        action = request.data.get('action')

        # ── set_fees ─────────────────────────────
        if action == 'set_fees':
            serializer = FeesSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            fees = serializer.save(student=student, paid_amount=0, payment_status='unpaid')
            return Response(
                {'message': f'Fees set for {student.name}.',
                 'fees': FeesSerializer(fees).data},
                status=status.HTTP_201_CREATED,
            )

        if not fees:
            return Response(
                {'error': 'No fee record found for this student.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # ── update_fees ───────────────────────────
        if action == 'update_fees':
            serializer = FeesSerializer(fees, data=request.data, partial=True)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            fees = serializer.save(payment_status='unpaid')
            return Response({
                'message': f'Fees updated for {student.name}.',
                'fees':    FeesSerializer(fees).data,
            })

        # ── approve ───────────────────────────────
        elif action == 'approve':
            serializer = FeesSerializer(
                fees,
                data={'paid_amount': request.data.get('paid_amount', fees.total_fees)},
                partial=True,
            )
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            fees = serializer.save(payment_status='paid')
            send_mail(
                subject='Fee Payment Approved ✅',
                message=(
                    f"Dear {student.name},\n\n"
                    f"Your fee payment of ₹{fees.paid_amount} has been approved.\n\n"
                    f"Student Portal Team"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student.email],
                fail_silently=True,
            )
            return Response({'message': f"{student.name}'s payment approved."})

        # ── reject ────────────────────────────────
        elif action == 'reject':
            fees.payment_status = 'unpaid'
            fees.receipt_image  = None
            fees.payment_ref    = ''
            fees.save()
            send_mail(
                subject='Fee Payment Rejected ❌',
                message=(
                    f"Dear {student.name},\n\n"
                    f"Your receipt was rejected. Please resubmit.\n\n"
                    f"Student Portal Team"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student.email],
                fail_silently=True,
            )
            return Response({'message': f"{student.name}'s payment rejected."})

        return Response({'error': 'Invalid action.'}, status=status.HTTP_400_BAD_REQUEST)


# ═════════════════════════════════════════════
#  MANAGEMENT — FEE REMINDERS
# ═════════════════════════════════════════════

class ManagementTriggerRemindersAPI(APIView):
    """
    POST /api/management/reminders/
    Sends fee reminder emails to all students with pending dues.
    """
    permission_classes = [IsManagementSession]

    def post(self, request):
        all_fees = Fees.objects.select_related('student').all()
        sent     = 0

        for fee in all_fees:
            due_amount = fee.total_fees - fee.paid_amount
            if due_amount > 0 and fee.student.email:
                send_mail(
                    subject='Fee Payment Reminder',
                    message=(
                        f"Dear {fee.student.name},\n\n"
                        f"You have a pending fee of ₹{due_amount}.\n\n"
                        f"Please pay and upload your receipt.\n\nStudent Portal Team"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[fee.student.email],
                    fail_silently=True,
                )
                sent += 1

        return Response({'message': f'Reminder emails sent to {sent} student(s).'})