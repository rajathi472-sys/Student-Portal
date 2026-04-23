from django.db import models
from django.contrib.auth.hashers import make_password, is_password_usable

class Teacher(models.Model):
    teacher_id = models.CharField(max_length=20, unique=True)
    name       = models.CharField(max_length=50)
    password   = models.CharField(max_length=255) 
    department = models.CharField(max_length=100)
    def save(self, *args, **kwargs):
        if not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name



class Student(models.Model):
    roll_no    = models.CharField(max_length=20,unique=True )
    name       = models.CharField(max_length=100)
    contact    = models.CharField(max_length=10)
    department = models.CharField(max_length=100)
    college    = models.CharField(max_length=200)
    email      = models.EmailField(blank=True, null=True)   
    teacher    = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    password   = models.CharField(max_length=255, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
    def __str__(self):
        return str(self.roll_no)

class CGPA(models.Model):
    SUB_TYPE_CHOICES = [('theory', 'Theory'), ('lab', 'Lab')]
    GRADE_CHOICES    = [('O','O'),('A+','A+'),('A','A'),('B+','B+'),('B','B'),('C','C'),('F','F')]
    student  = models.ForeignKey(Student, on_delete=models.CASCADE)
    semester = models.CharField(max_length=20)
    subject  = models.CharField(max_length=100)
    grade    = models.CharField(max_length=3, choices=GRADE_CHOICES)
    credits  = models.FloatField(default=0)
    sub_type = models.CharField(max_length=10, choices=SUB_TYPE_CHOICES, default='theory')

    class Meta:
        unique_together = ('student', 'semester', 'subject')

    def __str__(self):
        return f"{self.student.roll_no} - {self.subject} - Sem {self.semester}"



class Fees(models.Model):
    STATUS_CHOICES = [
        ('unpaid',  'Unpaid'),
        ('pending', 'Pending Verification'),
        ('paid',    'Paid'),
    ]
    student        = models.OneToOneField(Student, on_delete=models.CASCADE)
    total_fees     = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unpaid')
    payment_ref    = models.CharField(max_length=100, blank=True)
    receipt_image  = models.ImageField(upload_to='receipts/', blank=True, null=True)
    payment_date   = models.DateField(null=True, blank=True)
    due_date       = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.name} - {self.payment_status}"

class Admin(models.Model):
    id         = models.AutoField(primary_key=True)
    admin_id  = models.CharField(max_length=20, unique=True)
    name      = models.CharField(max_length=50)
    password  = models.CharField(max_length=255)

    def __str__(self):
        return self.name

# ── Add these models to your existing models.py ──────────────────


class Management(models.Model):
    id         = models.AutoField(primary_key=True)
    management_id = models.CharField(max_length=20, unique=True)
    name          = models.CharField(max_length=50)
    email         = models.EmailField(unique=True)
    password      = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        if not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

