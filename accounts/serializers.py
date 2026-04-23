from rest_framework import serializers
from .models import Student, Teacher, Fees, CGPA, Management


# ─────────────────────────────────────────────
#  TEACHER
# ─────────────────────────────────────────────

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Teacher
        fields = ['id', 'teacher_id', 'name', 'department']


# ─────────────────────────────────────────────
#  STUDENT
# ─────────────────────────────────────────────

class StudentSerializer(serializers.ModelSerializer):
    teacher = TeacherSerializer(read_only=True)
    teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=Teacher.objects.all(),
        source='teacher',
        write_only=True,
    )
    password = serializers.CharField(write_only=True)

    class Meta:
        model  = Student
        fields = [
            'id', 'roll_no', 'name', 'email',
            'contact', 'department', 'college',
            'teacher', 'teacher_id', 'password',
        ]

    def validate_name(self, value):
        if any(c.isdigit() for c in value):
            raise serializers.ValidationError("Name should not contain numbers.")
        return value

    def validate_contact(self, value):
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError("Contact must be exactly 10 digits.")
        return value

    def validate_roll_no(self, value):
        # On update, exclude the current instance from the uniqueness check
        qs = Student.objects.filter(roll_no=value)
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.exists():
            raise serializers.ValidationError(f"Roll number {value} already exists.")
        return value


# ─────────────────────────────────────────────
#  CGPA
# ─────────────────────────────────────────────

class CGPASerializer(serializers.ModelSerializer):
    class Meta:
        model  = CGPA
        fields = ['id', 'semester', 'subject', 'grade', 'credits', 'sub_type']


# ─────────────────────────────────────────────
#  FEES
# ─────────────────────────────────────────────

class FeesSerializer(serializers.ModelSerializer):
    due_amount    = serializers.SerializerMethodField()
    receipt_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model  = Fees
        fields = [
            'id', 'total_fees', 'paid_amount', 'due_amount',
            'payment_status', 'due_date', 'payment_ref',
            'payment_date', 'receipt_image',
        ]

    def get_due_amount(self, obj):
        return obj.total_fees - obj.paid_amount

    def validate_total_fees(self, value):
        if value < 0:
            raise serializers.ValidationError("Total fees cannot be negative.")
        if value > 9_999_999:
            raise serializers.ValidationError("Total fees cannot exceed ₹9,999,999.")
        return value

    def validate_paid_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Paid amount cannot be negative.")
        if value > 9_999_999:
            raise serializers.ValidationError("Paid amount cannot exceed ₹9,999,999.")
        return value

    def validate_receipt_image(self, value):
        if value:
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Receipt image must be less than 5 MB.")
            if value.content_type not in ['image/jpeg', 'image/jpg', 'image/png']:
                raise serializers.ValidationError("Only JPG and PNG images are allowed.")
        return value

    def validate_due_date(self, value):
        if value and value.year > 2026:
            raise serializers.ValidationError("Due date cannot be beyond 2026.")
        return value

    def validate(self, data):
        # Cross-field: paid cannot exceed total
        total = data.get('total_fees', getattr(self.instance, 'total_fees', 0))
        paid  = data.get('paid_amount', getattr(self.instance, 'paid_amount', 0))
        if paid > total:
            raise serializers.ValidationError(
                {'paid_amount': f"Paid amount ₹{paid} cannot exceed total fees ₹{total}."}
            )
        return data


# ─────────────────────────────────────────────
#  RECEIPT SUBMIT  (student-facing, limited fields)
# ─────────────────────────────────────────────

class ReceiptSubmitSerializer(serializers.Serializer):
    payment_ref   = serializers.CharField(max_length=100)
    payment_date  = serializers.DateField()
    receipt_image = serializers.ImageField()

    def validate_receipt_image(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Receipt image must be less than 5 MB.")
        if value.content_type not in ['image/jpeg', 'image/jpg', 'image/png']:
            raise serializers.ValidationError("Only JPG and PNG images are allowed.")
        return value


# ─────────────────────────────────────────────
#  AUTH
# ─────────────────────────────────────────────

class StudentLoginSerializer(serializers.Serializer):
    roll_no  = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate_roll_no(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Invalid User ID.")
        return value


class ManagementLoginSerializer(serializers.Serializer):
    management_id = serializers.CharField()
    password      = serializers.CharField(write_only=True)