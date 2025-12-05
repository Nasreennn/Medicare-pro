from django.db import models
from django.contrib.auth.models import AbstractUser

# ---------------------------
# CUSTOM USER
# ---------------------------
class User(AbstractUser):
    is_doctor = models.BooleanField(default=False)
    is_patient = models.BooleanField(default=False)

    def __str__(self):
        return self.username


# ---------------------------
# DOCTOR
# ---------------------------
class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    specialization = models.CharField(max_length=100, blank=True)
    qualification = models.CharField(max_length=200, blank=True)
    experience = models.IntegerField(default=0)
    bio = models.TextField(blank=True)
    clinic_address = models.CharField(max_length=255, blank=True)
    timings = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.user.get_full_name()




# ---------------------------
# PATIENT
# ---------------------------
class Patient(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    user = models.OneToOneField(   # <-- FIXED: Only 1 patient per user
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'is_patient': True}  # <-- Show only patient users
    )
    phone = models.CharField(max_length=15)
    age = models.IntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='Male')

    def __str__(self):
        return f"{self.user.username} - {self.phone}"


# ---------------------------
# APPOINTMENT
# ---------------------------
class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    date_time = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('Pending', 'Pending'),
            ('Confirmed', 'Confirmed'),
            ('Completed', 'Completed'),
            ('Rejected', 'Rejected'),
            
        ],
        default='Pending'
    )

    def __str__(self):
        return f"{self.patient} with {self.doctor} on {self.date_time}"


# ---------------------------
# MEDICAL RECORD
# ---------------------------
class MedicalRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Record for {self.patient} by {self.doctor}"



