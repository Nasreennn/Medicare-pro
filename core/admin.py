from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Doctor, Patient, Appointment, MedicalRecord

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Roles', {'fields': ('is_doctor', 'is_patient')}),
    )

    list_display = ('username', 'email', 'is_doctor', 'is_patient', 'is_staff')
    list_filter = ('is_doctor', 'is_patient', 'is_staff')


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'specialization')
    list_filter = ('specialization',)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'age', 'gender')
    list_filter = ('gender',)


admin.site.register(Appointment)
admin.site.register(MedicalRecord)
