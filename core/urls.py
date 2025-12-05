from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Home page
    path('', views.home, name='home'),
    path('index/', views.home, name='index'),

    # Authentication
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard (after login)
    path('dashboard/', views.dashboard, name='dashboard'),

    # Patients
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/new/', views.patient_create, name='patient_create'),
    path('patients/<int:pk>/', views.patient_profile, name='patient_profile'),
    path('patients/<int:pk>/edit/', views.patient_edit, name='patient_edit'),
    path('patients/<int:pk>/delete/', views.patient_delete, name='patient_delete'),

    # Appointments
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/new/', views. appointment_create, name='appointment_create'),
    path('appointments/<int:id>/edit/', views. appointment_edit, name='appointment_edit'),
    path('appointments/<int:id>/', views. appointment_detail, name='appointment_detail'),

    # ✅ NEW Doctor URLs
    path('doctors/<int:pk>/', views.doctor_profile, name='doctor_profile'),
    path('doctors/', views.doctor_list, name='doctor_list'),


    path('services/', views.services, name='services'),
    path('contact/', views.contact, name='contact'),

    path('record/add/<int:patient_id>/', views.record_create, name='record_create'),

    path('appointments/<int:pk>/approve/', views.approve_appointment, name='approve_appointment'),
    path('appointments/<int:pk>/reject/', views.reject_appointment, name='reject_appointment'),

    
    
    # Admin – view all medical records
    path('records/', views.record_list, name='record_list'),

    path('record/<int:pk>/delete/', views.record_delete, name='record_delete'),
    path('record/<int:pk>/pdf/', views.record_pdf, name='record_pdf'),

   
    
    



]
    
