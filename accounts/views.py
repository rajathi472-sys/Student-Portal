from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from django.conf import settings
from .models import Student, Fees, CGPA, Teacher, Management
from datetime import datetime, date

GRADE_POINTS = {
    'O':  10,
    'A+':  9,
    'A':   8,
    'B+':  7,
    'B':   6,
    'C':   5,
    'F':   0,
}


# ─────────────────────────────────────────────
#  MANAGEMENT AUTH GUARD (helper)
# ─────────────────────────────────────────────
def get_management(request):
    management_id = request.session.get('management_id')
    if not management_id:
        return None
    try:
        return Management.objects.get(management_id=management_id)
    except Management.DoesNotExist:
        return None


# ─────────────────────────────────────────────
#  HOME
# ─────────────────────────────────────────────
def home(request):
    return render(request, 'accounts/home.html')


# ─────────────────────────────────────────────
#  STUDENT LOGIN
# ─────────────────────────────────────────────
def student_login(request):
    if request.method == 'POST':
        roll_no  = request.POST['roll_no']
        password = request.POST['password']

        if not roll_no.isdigit():
            messages.error(request, "Invalid User ID")
            return redirect('student_login')

        try:
            student = Student.objects.get(roll_no=roll_no)
        except Student.DoesNotExist:
            messages.error(request, "Invalid Roll Number")
            return redirect('student_login')

        if not check_password(password, student.password):
            messages.error(request, "Invalid Password")
            return redirect('student_login')

        request.session['roll_no'] = roll_no
        return redirect('student_dashboard')

    return render(request, 'accounts/student_login.html')


# ─────────────────────────────────────────────
#  STUDENT DASHBOARD
# ─────────────────────────────────────────────
def student_dashboard(request):
    roll_no = request.session.get('roll_no')
    if not roll_no:
        return redirect('student_login')

    student = Student.objects.get(roll_no=roll_no)
    return render(request, 'accounts/student_dashboard.html', {'student': student})


# ─────────────────────────────────────────────
#  VIEW CGPA
# ─────────────────────────────────────────────
def view_cgpa(request):
    roll_no = request.session.get('roll_no')
    if not roll_no:
        return redirect('student_login')

    student = Student.objects.get(roll_no=roll_no)
    cgpa    = CGPA.objects.filter(student=student)

    total_credits      = sum(GRADE_POINTS.get(c.grade, 0) * c.credits for c in cgpa)
    total_credit_units = sum(c.credits for c in cgpa)
    overall_cgpa       = round(total_credits / total_credit_units, 2) if total_credit_units > 0 else 0

    semesters = {}
    for c in cgpa:
        if c.semester not in semesters:
            semesters[c.semester] = {'subjects': [], 'credits': 0, 'points': 0}
        semesters[c.semester]['subjects'].append(c)
        semesters[c.semester]['credits'] += c.credits
        semesters[c.semester]['points']  += GRADE_POINTS.get(c.grade, 0) * c.credits

    for sem in semesters:
        semesters[sem]['cgpa'] = round(
            semesters[sem]['points'] / semesters[sem]['credits'], 2
        ) if semesters[sem]['credits'] > 0 else 0

    return render(request, 'accounts/cgpa.html', {
        'student':      student,
        'semesters':    semesters,
        'overall_cgpa': overall_cgpa,
    })


# ─────────────────────────────────────────────
#  VIEW FEES
# ─────────────────────────────────────────────
def view_fees(request):
    roll_no = request.session.get('roll_no')
    if not roll_no:
        return redirect('student_login')

    student    = Student.objects.get(roll_no=roll_no)
    fees       = Fees.objects.filter(student=student).first()
    due_amount = fees.total_fees - fees.paid_amount if fees else None

    if request.method == 'POST' and fees:
        receipt = request.FILES.get('receipt_image')

        # ── File size check ──
        if receipt:
            if receipt.size > 5 * 1024 * 1024:  # 5MB in bytes
                messages.error(request, "Receipt image must be less than 5MB.")
                return redirect('view_fees')

            # ── File type check ──
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
            if receipt.content_type not in allowed_types:
                messages.error(request, "Only JPG and PNG images are allowed.")
                return redirect('view_fees')

        fees.payment_ref    = request.POST.get('payment_ref')
        fees.payment_date   = request.POST.get('payment_date')
        fees.receipt_image  = receipt
        fees.payment_status = 'pending'
        fees.save()
        messages.success(request, "Receipt submitted! Awaiting verification.")
        return redirect('view_fees')

    return render(request, 'accounts/fees.html', {
        'fees':       fees,
        'due_amount': due_amount,
        'student':    student,
    })


# ─────────────────────────────────────────────
#  TEACHER LOGIN
# ─────────────────────────────────────────────
def teacher_login(request):
    if request.method == 'POST':
        teacher_id = request.POST['teacher_id']
        password   = request.POST['password']

        try:
            teacher = Teacher.objects.get(teacher_id=teacher_id)
        except Teacher.DoesNotExist:
            messages.error(request, "Invalid credentials")
            return redirect('teacher_login')

        if not check_password(password, teacher.password):
            messages.error(request, "Invalid credentials")
            return redirect('teacher_login')

        request.session['teacher_id'] = teacher_id
        return redirect('teacher_dashboard')

    return render(request, 'accounts/teacher_login.html')


# ─────────────────────────────────────────────
#  TEACHER DASHBOARD
# ─────────────────────────────────────────────
def teacher_dashboard(request):
    teacher_id = request.session.get('teacher_id')
    if not teacher_id:
        return redirect('teacher_login')

    teacher  = Teacher.objects.get(teacher_id=teacher_id)
    students = Student.objects.filter(teacher=teacher)

    return render(request, 'accounts/teacher_dashboard.html', {
        'teacher':  teacher,
        'students': students,
    })

# ─────────────────────────────────────────────
#  TEACHER EDIT CGPA
# ─────────────────────────────────────────────
def teacher_edit_student(request, id):
    teacher_id = request.session.get('teacher_id')
    if not teacher_id:
        return redirect('teacher_login')

    teacher = Teacher.objects.get(teacher_id=teacher_id)

    try:
        student = Student.objects.get(id=id, teacher=teacher)
    except Student.DoesNotExist:
        messages.error(request, "You are not allowed to access this student.")
        return redirect('teacher_dashboard')

    if request.method == 'POST':
        type = request.POST.get('type')

        # 🔐 Restrict actions
        if type not in ['update_cgpa', 'add_cgpa', 'delete_cgpa']:
            messages.error(request, "You are not allowed to modify student details.")
            return redirect('teacher_dashboard')

        if type == 'update_cgpa':
            cgpa_id = request.POST.get('id')
            grade   = request.POST.get('grade', '').strip()
            credit  = request.POST.get('credits', '').strip()
            subtype = request.POST.get('sub_type', 'theory')

            if grade and credit:
                try:
                    cgpa_obj = CGPA.objects.get(id=cgpa_id, student=student)
                    cgpa_obj.grade = grade
                    cgpa_obj.credits = float(credit)
                    cgpa_obj.sub_type = subtype
                    cgpa_obj.save()
                    messages.success(request, f"{cgpa_obj.subject} updated successfully.")
                except CGPA.DoesNotExist:
                    messages.error(request, "Record not found.")
            else:
                messages.error(request, "Grade and credits are required.")

        elif type == 'add_cgpa':
            semester = request.POST.get('semester', '').strip()

            if not semester:
                messages.error(request, "Please enter a semester number.")
                return redirect('teacher_edit_student', id=id)

            subjects     = request.POST.getlist('subject')
            grades       = request.POST.getlist('grade')
            credits_list = request.POST.getlist('credits')
            sub_types    = request.POST.getlist('sub_type')

            saved = 0
            for i in range(len(subjects)):
                subj    = subjects[i].strip() if i < len(subjects) else ''
                grade   = grades[i].strip() if i < len(grades) else ''
                credit  = credits_list[i].strip() if i < len(credits_list) else ''
                subtype = sub_types[i] if i < len(sub_types) else 'theory'

                if subj and grade and credit:
                    if not credit.isdigit():
                        messages.error(request, f"Credits for '{subj}' must be a whole number.")
                        return redirect('teacher_edit_student', id=id)

                    if int(credit) >= 5:
                            messages.error(request, f"Credits for '{subj}' must be below 5.")
                            return redirect('teacher_edit_student', id=id)

                    CGPA.objects.update_or_create(
                        student=student,
                        semester=semester,
                        subject=subj,
                        defaults={
                            'grade': grade,
                            'credits': int(credit),
                            'sub_type': subtype,
                        }
                    )
                    saved += 1

            if saved > 0:
                messages.success(request, f"{saved} subject(s) saved for Semester {semester}.")
            else:
                messages.error(request, "No subjects saved.")

        elif type == 'delete_cgpa':
            CGPA.objects.filter(id=request.POST.get('id'), student=student).delete()
            messages.success(request, "Record deleted.")

        return redirect('teacher_edit_student', id=id)

    # CGPA calculation (unchanged ✅)
    cgpa = CGPA.objects.filter(student=student)

    total_credits = sum(GRADE_POINTS.get(c.grade, 0) * c.credits for c in cgpa)
    total_credit_units = sum(c.credits for c in cgpa)
    overall_cgpa = round(total_credits / total_credit_units, 2) if total_credit_units > 0 else 0

    semesters = {}
    for c in cgpa:
        if c.semester not in semesters:
            semesters[c.semester] = {'subjects': [], 'credits': 0, 'points': 0}
        semesters[c.semester]['subjects'].append(c)
        semesters[c.semester]['credits'] += c.credits
        semesters[c.semester]['points'] += GRADE_POINTS.get(c.grade, 0) * c.credits

    for sem in semesters:
        semesters[sem]['cgpa'] = round(
            semesters[sem]['points'] / semesters[sem]['credits'], 2
        ) if semesters[sem]['credits'] > 0 else 0

    return render(request, 'accounts/edit_student.html', {
        'student': student,
        'cgpa': cgpa,
        'semesters': semesters,
        'overall_cgpa': overall_cgpa,
        'grade_choices': ['O', 'A+', 'A', 'B+', 'B', 'C', 'F'],
    })
# ─────────────────────────────────────────────
#  MANAGEMENT LOGIN
# ─────────────────────────────────────────────
def management_login(request):
    if request.method == 'POST':
        management_id = request.POST['management_id']
        password      = request.POST['password']

        try:
            management = Management.objects.get(management_id=management_id)
        except Management.DoesNotExist:
            messages.error(request, "Invalid credentials")
            return redirect('management_login')

        if not check_password(password, management.password):
            messages.error(request, "Invalid credentials")
            return redirect('management_login')

        request.session['management_id'] = management_id
        return redirect('management_dashboard')

    return render(request, 'accounts/management_login.html')


# ─────────────────────────────────────────────
#  MANAGEMENT DASHBOARD
# ─────────────────────────────────────────────
def management_dashboard(request):
    management = get_management(request)
    if not management:
        return redirect('management_login')

    students = Student.objects.all().order_by('name')

    student_data = []
    for student in students:
        fees       = Fees.objects.filter(student=student).first()
        due_amount = (fees.total_fees - fees.paid_amount) if fees else None
        status     = fees.payment_status if fees else 'no_fees'
        student_data.append({
            'student':    student,
            'fees':       fees,
            'due_amount': due_amount,
            'status':     status,
        })

    return render(request, 'accounts/management_dashboard.html', {
        'management':     management,
        'student_data':   student_data,
        'total_students': students.count(),
        'teacher_count':  Teacher.objects.count(),
        'pending_count':  Fees.objects.filter(payment_status='pending').count(),
        'paid_count':     Fees.objects.filter(payment_status='paid').count(),
        'unpaid_count':   Fees.objects.filter(payment_status='unpaid').count(),
    })


# ─────────────────────────────────────────────
#  MANAGEMENT STUDENT FEES DETAIL
# ─────────────────────────────────────────────
def management_student_fees_detail(request, student_id):
    management = get_management(request)
    if not management:
        return redirect('management_login')

    student    = Student.objects.get(id=student_id)
    fees       = Fees.objects.filter(student=student).first()
    due_amount = (fees.total_fees - fees.paid_amount) if fees else None

    if request.method == 'POST':
        action = request.POST.get('action')

        def validate_amount(value, field_name="Amount"):
            if not value or str(value).strip() == '':
                return None, f"{field_name} is required."
            try:
                amount = int(float(str(value).strip()))
            except (ValueError, TypeError):
                return None, f"{field_name} must be a valid number."
            if amount < 0:
                return None, f"{field_name} cannot be negative."
            if amount > 9999999:
                return None, f"{field_name} cannot exceed 7 digits (max ₹9,999,999)."
            return amount, None

        def validate_due_date(due_date):
            if not due_date or str(due_date).strip() == '':
                return None, "Due date is required."
            try:
                date_obj = datetime.strptime(due_date, "%Y-%m-%d")
                if date_obj.year > 2026:
                    return None, "Due date cannot be beyond 2026."
                return due_date, None
            except ValueError:
                return None, "Due date is invalid."

        if action == 'set_fees':
            total_fees, error = validate_amount(request.POST.get('total_fees'), "Total fees")
            if error:
                messages.error(request, error)
                return redirect('management_student_fees_detail', student_id=student.id)

            due_date, error = validate_due_date(request.POST.get('due_date'))
            if error:
                messages.error(request, error)
                return redirect('management_student_fees_detail', student_id=student.id)
            Fees.objects.create(
                student        = student,
                total_fees     = total_fees,
                paid_amount    = 0,
                payment_status = 'unpaid',
                due_date       = due_date,
            )

        elif action == 'update_fees' and fees:
            total_fees, error = validate_amount(request.POST.get('total_fees'), "Total fees")
            if error:
                messages.error(request, error)
                return redirect('management_student_fees_detail', student_id=student.id)

            due_date, error = validate_due_date(request.POST.get('due_date'))
            if error:
                messages.error(request, error)
                return redirect('management_student_fees_detail', student_id=student.id)

            fees.total_fees     = total_fees
            fees.due_date       = due_date
            fees.payment_status = 'unpaid'
            fees.save()
            messages.success(request, f"Fees updated for {student.name}.")

        elif action == 'approve' and fees:
            paid_amount, error = validate_amount(
                request.POST.get('paid_amount') or str(fees.total_fees),
                "Paid amount"
            )
            if error:
                messages.error(request, error)
                return redirect('management_student_fees_detail', student_id=student.id)

            if paid_amount > int(fees.total_fees):
                messages.error(request, f"Paid amount ₹{paid_amount} cannot exceed total fees ₹{fees.total_fees}.")
                return redirect('management_student_fees_detail', student_id=student.id)

            fees.paid_amount    = paid_amount
            fees.payment_status = 'paid'
            fees.save()

            send_mail(
                subject        = 'Fee Payment Approved ✅',
                message        = f"Dear {student.name},\n\nYour fee payment of ₹{paid_amount} has been approved.\n\nStudent Portal Team",
                from_email     = settings.DEFAULT_FROM_EMAIL,
                recipient_list = [student.email],
                fail_silently  = True,
            )
            messages.success(request, f"{student.name}'s payment approved.")

        elif action == 'reject' and fees:
            fees.payment_status = 'unpaid'
            fees.receipt_image  = None
            fees.payment_ref    = ''
            fees.save()

            send_mail(
                subject        = 'Fee Payment Rejected ❌',
                message        = f"Dear {student.name},\n\nYour receipt was rejected. Please resubmit.\n\nStudent Portal Team",
                from_email     = settings.DEFAULT_FROM_EMAIL,
                recipient_list = [student.email],
                fail_silently  = True,
            )
            messages.error(request, f"{student.name}'s payment rejected.")

        return redirect('management_student_fees_detail', student_id=student.id)

    return render(request, 'accounts/management_student_fees_detail.html', {
        'student':    student,
        'fees':       fees,
        'due_amount': due_amount,
    })


# ─────────────────────────────────────────────
#  SEND FEE REMINDERS
# ─────────────────────────────────────────────
def trigger_reminders(request):
    management = get_management(request)
    if not management:
        return redirect('management_login')

    all_fees = Fees.objects.select_related('student').all()
    sent     = 0

    for fee in all_fees:
        due_amount = fee.total_fees - fee.paid_amount
        if due_amount > 0 and fee.student.email:
            try:
                send_mail(
                    subject        = 'Fee Payment Reminder',
                    message        = f"Dear {fee.student.name},\n\nYou have a pending fee of Rs.{due_amount}.\n\nPlease pay and upload your receipt.\n\nStudent Portal Team",
                    from_email     = settings.DEFAULT_FROM_EMAIL,
                    recipient_list = [fee.student.email],
                    fail_silently  = True,
                )
                sent += 1
            except Exception:
                pass

    messages.success(request, f"Reminder emails sent to {sent} students with pending fees.")
    return redirect('management_dashboard')


# ─────────────────────────────────────────────
#  MANAGEMENT STUDENTS — List
# ─────────────────────────────────────────────
def management_students(request):
    management = get_management(request)
    if not management:
        return redirect('management_login')

    students = Student.objects.select_related('teacher').all().order_by('roll_no')
    teachers = Teacher.objects.all()

    return render(request, 'accounts/management_students.html', {
        'management': management,
        'students':   students,
        'teachers':   teachers,
    })


# ─────────────────────────────────────────────
#  MANAGEMENT STUDENTS — Add
# ─────────────────────────────────────────────
def management_add_student(request):
    management = get_management(request)
    if not management:
        return redirect('management_login')

    if request.method == 'POST':
        roll_no    = request.POST.get('roll_no')
        name       = request.POST.get('name')
        contact    = request.POST.get('contact')
        department = request.POST.get('department')
        college    = request.POST.get('college')
        email      = request.POST.get('email')
        password   = request.POST.get('password')
        teacher_id = request.POST.get('teacher_id')

        if any(char.isdigit() for char in name):
            messages.error(request, "Name should not contain numbers.")
            return redirect('management_add_student')

        if Student.objects.filter(roll_no=roll_no).exists():
            messages.error(request, f"Roll number {roll_no} already exists.")
            return redirect('management_add_student')

        if not contact.isdigit() or len(contact) != 10:
            messages.error(request, "Contact must be exactly 10 digits.")
            return redirect('management_add_student')

        try:
            teacher = Teacher.objects.get(id=teacher_id)
        except Teacher.DoesNotExist:
            messages.error(request, "Selected teacher not found.")
            return redirect('management_add_student')

        student = Student.objects.create(
            roll_no    = roll_no,
            name       = name,
            contact    = contact,
            department = department,
            college    = college,
            email      = email,
            password   = password,
            teacher    = teacher,
        )

        Fees.objects.create(
            student        = student,
            total_fees     = 0,
            paid_amount    = 0,
            payment_status = 'unpaid',
        )

        messages.success(request, f"Student {name} added successfully.")
        return redirect('management_students')

    teachers = Teacher.objects.all()
    return render(request, 'accounts/management_add_student.html', {
        'management': management,
        'teachers':   teachers,
    })


# ─────────────────────────────────────────────
#  MANAGEMENT STUDENTS — Edit
# ─────────────────────────────────────────────
def management_edit_student(request, id):
    management = get_management(request)
    if not management:
        return redirect('management_login')

    try:
        student = Student.objects.get(id=id)
    except Student.DoesNotExist:
        messages.error(request, "Student not found.")
        return redirect('management_students')

    if request.method == 'POST':
        name       = request.POST.get('name',       student.name)
        contact    = request.POST.get('contact',    student.contact)
        department = request.POST.get('department', student.department)
        college    = request.POST.get('college',    student.college)
        email      = request.POST.get('email',      student.email)
        roll_no    = request.POST.get('roll_no',    student.roll_no)
        teacher_id = request.POST.get('teacher_id')
        password   = request.POST.get('password', '').strip()

        # Validate name
        if any(char.isdigit() for char in name):
            messages.error(request, "Name should not contain numbers.")
            return redirect('management_edit_student', id=id)

        # Validate contact
        if not contact.isdigit() or len(contact) != 10:
            messages.error(request, "Contact must be exactly 10 digits.")
            return redirect('management_edit_student', id=id)

        # Validate roll_no unique
        # check if another student already has this roll_no
        if Student.objects.filter(roll_no=roll_no).exclude(id=id).exists():
            messages.error(request, f"Roll number {roll_no} already exists.")
            return redirect('management_edit_student', id=id)

        student.name       = name
        student.contact    = contact
        student.department = department
        student.college    = college
        student.email      = email
        student.roll_no    = roll_no  # ← NOW saving roll_no

        # Update password only if new one entered
        if password:
            student.password = password

        # Update teacher
        if teacher_id:
            try:
                student.teacher = Teacher.objects.get(id=teacher_id)
            except Teacher.DoesNotExist:
                messages.error(request, "Selected teacher not found.")
                return redirect('management_edit_student', id=id)

        student.save()
        messages.success(request, f"Student {student.name} updated successfully.")
        return redirect('management_students')

    teachers = Teacher.objects.all()
    return render(request, 'accounts/management_edit_student.html', {
        'management': management,
        'student':    student,
        'teachers':   teachers,
    })

# ─────────────────────────────────────────────
#  MANAGEMENT STUDENTS — Delete
# ─────────────────────────────────────────────
def management_delete_student(request, id):
    management = get_management(request)
    if not management:
        return redirect('management_login')

    try:
        student = Student.objects.get(id=id)
        name    = student.name
        student.delete()
        messages.success(request, f"Student {name} deleted successfully.")
    except Student.DoesNotExist:
        messages.error(request, "Student not found.")

    return redirect('management_students')


# ─────────────────────────────────────────────
#  MANAGEMENT TEACHERS — List
# ─────────────────────────────────────────────
def management_teachers(request):
    management = get_management(request)
    if not management:
        return redirect('management_login')

    teachers = Teacher.objects.all().order_by('name')

    return render(request, 'accounts/management_teachers.html', {
        'management': management,
        'teachers':   teachers,
    })


# ─────────────────────────────────────────────
#  MANAGEMENT TEACHERS — Add
# ─────────────────────────────────────────────
def management_add_teacher(request):
    management = get_management(request)
    if not management:
        return redirect('management_login')

    if request.method == 'POST':
        teacher_id = request.POST.get('teacher_id')
        name       = request.POST.get('name')
        department = request.POST.get('department')
        password   = request.POST.get('password')

        if any(char.isdigit() for char in name):
            messages.error(request, "Name should not contain numbers.")
            return redirect('management_add_teacher')

        if Teacher.objects.filter(teacher_id=teacher_id).exists():
            messages.error(request, f"Teacher ID {teacher_id} already exists.")
            return redirect('management_add_teacher')

        Teacher.objects.create(
            teacher_id = teacher_id,
            name       = name,
            password   = make_password(password),
            department = department,
        )

        messages.success(request, f"Teacher {name} added successfully.")
        return redirect('management_teachers')

    return render(request, 'accounts/management_add_teacher.html', {
        'management': management,
    })


# ─────────────────────────────────────────────
#  MANAGEMENT TEACHERS — Edit
# ─────────────────────────────────────────────
def management_edit_teacher(request, id):
    management = get_management(request)
    if not management:
        return redirect('management_login')

    try:
        teacher = Teacher.objects.get(id=id)
    except Teacher.DoesNotExist:
        messages.error(request, "Teacher not found.")
        return redirect('management_teachers')

    if request.method == 'POST':
        teacher_id = request.POST.get('teacher_id', teacher.teacher_id).strip()
        name       = request.POST.get('name',       teacher.name).strip()
        department = request.POST.get('department', teacher.department).strip()
        password   = request.POST.get('password', '').strip()

        # Validate name
        if any(char.isdigit() for char in name):
            messages.error(request, "Name should not contain numbers.")
            return redirect('management_edit_teacher', id=id)

        # Validate teacher_id unique
        # exclude current teacher from duplicate check
        if Teacher.objects.filter(teacher_id=teacher_id).exclude(id=id).exists():
            messages.error(request, f"Teacher ID {teacher_id} already exists.")
            return redirect('management_edit_teacher', id=id)

        teacher.teacher_id = teacher_id  # ← NOW saving teacher_id
        teacher.name       = name
        teacher.department = department

        # Update password only if new one entered
        if password:
            teacher.password = make_password(password)

        teacher.save()
        messages.success(request, f"Teacher {teacher.name} updated successfully.")
        return redirect('management_teachers')

    return render(request, 'accounts/management_edit_teacher.html', {
        'management': management,
        'teacher':    teacher,
    })

# ─────────────────────────────────────────────
#  MANAGEMENT TEACHERS — Delete
# ─────────────────────────────────────────────
def management_delete_teacher(request, id):
    management = get_management(request)
    if not management:
        return redirect('management_login')

    try:
        teacher = Teacher.objects.get(id=id)
        name    = teacher.name
        teacher.delete()
        messages.success(request, f"Teacher {name} deleted successfully.")
    except Teacher.DoesNotExist:
        messages.error(request, "Teacher not found.")

    return redirect('management_teachers')


# ─────────────────────────────────────────────
#  LOGOUT
# ─────────────────────────────────────────────
def logout_view(request):
    request.session.flush()
    return redirect('/')