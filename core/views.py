from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import HttpResponseForbidden
from datetime import date
from .models import Patient, Appointment, Doctor, MedicalRecord
from .forms import PatientForm, AppointmentForm, MedicalRecordForm, SignupForm
from reportlab.pdfgen import canvas
from django.http import HttpResponse


# ---------------------------------------------------
# HOME PAGE (INDEX)
# ---------------------------------------------------
def home(request):
    return render(request, 'index.html')


def services(request):
    return render(request, 'services.html')

def contact(request):
    return render(request, 'contact.html')




# ---------------------------------------------------
# LOGIN VIEW
# ---------------------------------------------------
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('core:dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


# ---------------------------------------------------
# LOGOUT
# ---------------------------------------------------
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('core:login')


# ---------------------------------------------------
# SIGNUP (Patients only)
# ---------------------------------------------------
def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_patient = True
            user.save()

            # Create patient profile linked to user
            Patient.objects.create(
                user=user,
                phone='',
                age=0,
                gender='Other'
            )

            messages.success(request, "Account created successfully!")
            return redirect('core:login')
    else:
        form = SignupForm()

    return render(request, 'signup.html', {'form': form})



# ---------------------------------------------------
# ROLE-BASED DASHBOARD
# ---------------------------------------------------
@login_required
def dashboard(request):
    user = request.user

# ---------------------------------------------------
    # PATIENT DASHBOARD
    # -------------------------------
    if user.is_patient and not user.is_staff:
        patient = Patient.objects.get(user=user)

        appointments = Appointment.objects.filter(
            patient=patient
        ).order_by('-date_time')

        records = MedicalRecord.objects.filter(
            patient=patient
        ).order_by('-created_at')

        return render(request, 'dashboard_patient.html', {
            'patient': patient,
            'appointments': appointments,
            'records': records,
        })



    # DOCTOR DASHBOARD
    if user.is_doctor and not user.is_staff:
        doctor = Doctor.objects.get(user=user)

        appointments = Appointment.objects.filter(
            doctor=doctor
        ).order_by('-date_time')

        patients = Patient.objects.filter(
            appointment__doctor=doctor
        ).distinct()

        records = MedicalRecord.objects.filter(
            patient__appointment__doctor=doctor
        ).distinct()

        return render(request, 'dashboard_doctor.html', {
            'doctor': doctor,
            'appointments': appointments,
            'patients': patients,
            'records': records,
        })

    # ADMIN DASHBOARD
    if user.is_staff:
        from django.db.models import Count
        from collections import OrderedDict

        # --------- BASIC STATS ----------
        total_patients = Patient.objects.count()
        total_appointments = Appointment.objects.count()
        doctors_count = Doctor.objects.count()
        todays_appointments = Appointment.objects.filter(date_time__date=date.today())

        # --------- STATUS COUNTS (for pie chart) ----------
        # Initialize all to 0 so chart never breaks
        pending_count = 0
        confirmed_count = 0
        completed_count = 0
        rejected_count = 0

        status_qs = (
            Appointment.objects
            .values('status')
            .annotate(total=Count('id'))
        )

        for row in status_qs:
            status = row['status']
            total = row['total']
            if status == 'Pending':
                pending_count = total
            elif status == 'Confirmed':
                confirmed_count = total
            elif status == 'Completed':
                completed_count = total
            elif status == 'Rejected':
                rejected_count = total

        # --------- MONTHLY COUNTS (for bar chart) ----------
        monthly = OrderedDict()

        for appt in Appointment.objects.order_by('date_time'):
            # Example: "Dec 2025"
            label = appt.date_time.strftime('%b %Y')
            monthly[label] = monthly.get(label, 0) + 1

        month_labels = list(monthly.keys())
        month_counts = list(monthly.values())

        return render(request, 'dashboard_admin.html', {
            'total_patients': total_patients,
            'total_appointments': total_appointments,
            'doctors_count': doctors_count,
            'todays_appointments': todays_appointments,

            # chart data
            'pending_count': pending_count,
            'confirmed_count': confirmed_count,
            'completed_count': completed_count,
            'rejected_count': rejected_count,
            'month_labels': month_labels,
            'month_counts': month_counts,
        })



# ---------------------------------------------------
# PATIENT LIST (Doctors + Admin only)
# ---------------------------------------------------
@login_required
def patient_list(request):
    if request.user.is_patient and not request.user.is_staff:
        patient = Patient.objects.get(user=request.user)
        return redirect('core:patient_profile', pk=patient.pk)

    if not (request.user.is_doctor or request.user.is_staff):
        return HttpResponseForbidden("Not allowed.")

    patients = Patient.objects.all()
    return render(request, 'patients/patient_list.html', {'patients': patients})


# ---------------------------------------------------
# PATIENT CREATE
# ---------------------------------------------------
@login_required
def patient_create(request):
    if not (request.user.is_doctor or request.user.is_staff):
        return HttpResponseForbidden("Not allowed.")

    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Patient added successfully.")
            return redirect('core:patient_list')
    else:
        form = PatientForm()

    return render(request, 'patients/patient_form.html', {'form': form})


# ---------------------------------------------------
# PATIENT EDIT
# ---------------------------------------------------
@login_required
def patient_edit(request, pk):
    if not (request.user.is_doctor or request.user.is_staff):
        return HttpResponseForbidden("Not allowed.")

    patient = get_object_or_404(Patient, pk=pk)

    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, "Updated successfully.")
            return redirect('core:patient_profile', pk=pk)
    else:
        form = PatientForm(instance=patient)

    return render(request, 'patients/patient_form.html', {'form': form})


# ---------------------------------------------------
# PATIENT PROFILE
# ---------------------------------------------------
@login_required
def patient_profile(request, pk):
    patient = get_object_or_404(Patient, pk=pk)

    # ---------------------------
    # PATIENT ACCESS CONTROL FIX
    # ---------------------------
    if request.user.is_patient:

        # If patient tries to access someone else's page → BLOCK
        if request.user != patient.user:
            return HttpResponseForbidden("Not allowed.")

        # If patient tries to open their own profile through /patients/<id>/ → redirect
        return redirect('core:dashboard')

    # ---------------------------
    # DOCTOR / ADMIN CAN VIEW
    # ---------------------------
    print("🟦 USER:", patient.user.username)
    print("🟦 FULL NAME:", patient.user.get_full_name())
    print("🟦 EMAIL:", patient.user.email)

    records = MedicalRecord.objects.filter(patient=patient)
    appointments = Appointment.objects.filter(patient=patient)

    return render(request, 'patients/patient_profile.html', {
        'patient': patient,
        'records': records,
        'appointments': appointments,
    })




# ---------------------------------------------------
# DELETE PATIENT
# ---------------------------------------------------
@login_required
def patient_delete(request, pk):
    if not (request.user.is_doctor or request.user.is_staff):
        return HttpResponseForbidden("Not allowed.")

    patient = get_object_or_404(Patient, pk=pk)
    user = patient.user
    patient.delete()
    user.delete()

    messages.success(request, "Patient deleted.")
    return redirect('core:patient_list')


# ---------------------------------------------------
# APPOINTMENTS LIST
# ---------------------------------------------------
@login_required
def appointment_list(request):
    user = request.user

    if user.is_patient:
        patient = Patient.objects.get(user=user)
        appointments = Appointment.objects.filter(patient=patient)

    elif user.is_doctor:
        doctor = Doctor.objects.get(user=user)
        appointments = Appointment.objects.filter(doctor=doctor)

    else:
        appointments = Appointment.objects.all()

    return render(request, 'appointments/appointment_list.html', {
        'appointments': appointments
    })


# ---------------------------------------------------
# CREATE APPOINTMENT
# ---------------------------------------------------
# ---------------------------------------------------
# CREATE APPOINTMENT  (Patient → Pending)
# ---------------------------------------------------
@login_required
def appointment_create(request):

    if request.method == 'POST':
        form = AppointmentForm(request.POST)

        if form.is_valid():
            appointment = form.save(commit=False)

            # ---------------------------
            # Patient making appointment
            # ---------------------------
            if request.user.is_patient:
                appointment.patient = Patient.objects.get(user=request.user)
                appointment.status = "Pending"

            # ---------------------------
            # Doctor logged in
            # ---------------------------
            elif request.user.is_doctor:
                appointment.doctor = Doctor.objects.get(user=request.user)

            appointment.save()
            messages.success(request, "Appointment created successfully.")
            return redirect('core:appointment_list')

        else:
            print("FORM ERRORS:", form.errors)

    else:
        form = AppointmentForm()

    return render(request, 'appointments/appointment_form.html', {'form': form})


# ---------------------------------------------------
# EDIT APPOINTMENT
# ---------------------------------------------------
@login_required
def appointment_edit(request, id):
    appointment = get_object_or_404(Appointment, id=id)

    if request.user.is_patient and request.user != appointment.patient.user:
        return HttpResponseForbidden("Not allowed.")

    if request.method == 'POST':
        form = AppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, "Updated successfully.")
            return redirect('core:appointment_list')
    else:
        form = AppointmentForm(instance=appointment)

    return render(request, 'appointments/appointment_form.html', {'form': form})


# ---------------------------------------------------
# APPOINTMENT DETAIL
# ---------------------------------------------------
@login_required
def appointment_detail(request, id):
    appointment = get_object_or_404(Appointment, id=id)

    if request.user.is_patient and appointment.patient.user != request.user:
        return HttpResponseForbidden("Not allowed.")

    return render(request, 'appointments/appointment_detail.html', {'appointment': appointment})


# ===================================================
#   PATIENT ONLY PAGES
# ===================================================
@login_required
def my_profile(request):
    if not request.user.is_patient:
        return HttpResponseForbidden("Not allowed.")

    patient = Patient.objects.get(user=request.user)
    return render(request, 'patients/my_profile.html', {'patient': patient})


@login_required
def my_appointments(request):
    if not request.user.is_patient:
        return HttpResponseForbidden("Not allowed.")

    patient = Patient.objects.get(user=request.user)
    appointments = Appointment.objects.filter(patient=patient)

    return render(request, 'patients/my_appointments.html', {'appointments': appointments})



# ---------------------------------------------------
# APPOINTMENT APPROVAL (Doctor Only)
# ---------------------------------------------------
@login_required
def update_appointment_status(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)

    # Only the doctor of this appointment can change status
    if not request.user.is_doctor or appointment.doctor.user != request.user:
        return HttpResponseForbidden("Not allowed.")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "confirm":
            appointment.status = "Confirmed"
            appointment.save()
            messages.success(request, "Appointment confirmed successfully.")

        elif action == "reject":
            appointment.status = "Rejected"
            appointment.save()
            messages.success(request, "Appointment rejected successfully.")

        return redirect('core:dashboard')  # doctor dashboard

    return HttpResponseForbidden("Invalid request.")



@login_required
def my_records(request):
    if not request.user.is_patient:
        return HttpResponseForbidden("Not allowed.")

    patient = Patient.objects.get(user=request.user)
    records = MedicalRecord.objects.filter(patient=patient)

    return render(request, 'patients/my_records.html', {'records': records})




# ---------------------------------------------------
# DOCTOR LIST (Public)
# ---------------------------------------------------
def doctor_list(request):
    doctors = Doctor.objects.select_related('user').all()
    return render(request, 'doctors/doctor_list.html', {'doctors': doctors})


# ---------------------------------------------------
# DOCTOR PROFILE (Public)
# ---------------------------------------------------
def doctor_profile(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    return render(request, 'doctors/doctor_profile.html', {'doctor': doctor})


@login_required
def record_list(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("Only admin can access all medical records.")

    records = MedicalRecord.objects.select_related('patient', 'doctor', 'doctor__user').order_by('-created_at')

    return render(request, 'records/record_list.html', {
        'records': records
    })




@login_required
def record_create(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    # Only doctors can add medical notes
    if not request.user.is_doctor:
        return HttpResponseForbidden("Only doctors can add notes.")

    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.patient = patient
            record.doctor = Doctor.objects.get(user=request.user)
            record.save()
            messages.success(request, "Medical record added successfully.")
            return redirect('core:patient_profile', pk=patient_id)
        else:
            print("❌ FORM ERRORS:", form.errors)   # <-- THIS HELPS DEBUG
    else:
        form = MedicalRecordForm()

    return render(request, 'records/medicalrecord_form.html', {
        'form': form,
        'patient': patient
    })


# ---------------------------------------------------
# DELETE MEDICAL RECORD (Doctor/Admin only)
# ---------------------------------------------------
@login_required
def record_delete(request, pk):
    record = get_object_or_404(MedicalRecord, pk=pk)

    # Doctor can delete only his own record
    if request.user.is_doctor:
        doctor = Doctor.objects.get(user=request.user)
        if record.doctor != doctor:
            return HttpResponseForbidden("You cannot delete another doctor's note.")

    # Admin can delete everything
    if request.user.is_staff:
        pass

    patient_id = record.patient.id
    record.delete()

    messages.success(request, "Medical record deleted successfully.")
    return redirect('core:patient_profile', pk=patient_id)


# ---------------------------------------------------
# DOCTOR APPROVE / REJECT APPOINTMENT
# ---------------------------------------------------
@login_required
def approve_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)

    if not request.user.is_doctor or appointment.doctor.user != request.user:
        return HttpResponseForbidden("Not allowed.")

    appointment.status = "Confirmed"
    appointment.save()

    messages.success(request, "Appointment approved.")
    return redirect('core:appointment_list')


@login_required
def reject_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)

    if not request.user.is_doctor or appointment.doctor.user != request.user:
        return HttpResponseForbidden("Not allowed.")

    appointment.status = "Rejected"
    appointment.save()

    messages.success(request, "Appointment rejected.")
    return redirect('core:appointment_list')








# ---------------------------------------------------
# DOWNLOAD MEDICAL RECORD AS PDF
# ---------------------------------------------------

@login_required
def record_pdf(request, pk):
    record = get_object_or_404(MedicalRecord, pk=pk)

    # Permission checks
    if request.user.is_patient and record.patient.user != request.user:
        return HttpResponseForbidden("Not allowed.")
    if request.user.is_doctor and record.doctor.user != request.user:
        return HttpResponseForbidden("Not allowed.")

    response = HttpResponse(content_type='application/pdf')
    filename = f"MedicalRecord_{record.patient.user.get_full_name().replace(' ', '_')}.pdf"
    response['Content-Disposition'] = f'attachment; filename=\"{filename}\"'

    # Create PDF
    p = canvas.Canvas(response)
    p.setTitle("Medical Report")

    # ---------- HEADER ----------
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(300, 800, "MediCare Pro – Medical Report")

    p.setLineWidth(0.5)
    p.line(50, 785, 550, 785)

    # ---------- PATIENT INFO ----------
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, 760, "Patient Information:")

    p.setFont("Helvetica", 12)
    p.drawString(70, 740, f"Name: {record.patient.user.get_full_name()}")
    p.drawString(70, 720, f"Email: {record.patient.user.email}")
    p.drawString(70, 700, f"Phone: {record.patient.phone}")

    # ---------- DOCTOR INFO ----------
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, 670, "Doctor Information:")

    p.setFont("Helvetica", 12)
    p.drawString(70, 650, f"Doctor: {record.doctor.user.get_full_name()}")
    p.drawString(70, 630, f"Specialization: {record.doctor.specialization}")

    # ---------- MEDICAL NOTE ----------
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, 600, "Medical Note:")

    from reportlab.platypus import Paragraph, Frame
    from reportlab.lib.styles import getSampleStyleSheet

    styles = getSampleStyleSheet()
    style = styles["Normal"]
    style.fontSize = 12
    style.leading = 16

    # Wrap long text
    note_text = record.description.replace("\n", "<br/>")
    paragraph = Paragraph(note_text, style)

    # Large text area (no overlapping)
    frame = Frame(50, 260, 500, 320, showBoundary=0)
    frame.addFromList([paragraph], p)

    # ---------- FOOTER ----------
    p.setFont("Helvetica", 11)
    p.drawString(50, 220, f"Created on: {record.created_at.strftime('%b %d, %Y – %I:%M %p')}")
    p.drawString(50, 205, f"Doctor: {record.doctor.user.get_full_name()}")

    # Signature line (ONLY ONCE)
    p.line(50, 180, 250, 180)
    p.drawString(50, 165, "Doctor Signature")

    p.showPage()
    p.save()
    return response








   



   