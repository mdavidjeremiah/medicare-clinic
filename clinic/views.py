from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count, Q
from .models import PatientProfile, DoctorProfile, Appointment, MedicalRecord, ContactMessage, DoctorSchedule
from .forms import (PatientRegistrationForm, AppointmentForm, AppointmentStatusForm,
                    MedicalRecordForm, ContactForm, DoctorScheduleForm)
import datetime

def home(request):
    doctors = DoctorProfile.objects.select_related('user').all()[:4]
    return render(request, 'clinic/home.html', {'doctors': doctors})

def register(request):
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to MediCare Clinic.')
            return redirect('dashboard')
    else:
        form = PatientRegistrationForm()
    return render(request, 'clinic/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'clinic/login.html')

@login_required
def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')

@login_required
def dashboard(request):
    user = request.user
    if user.is_staff:
        return redirect('admin_dashboard')
    try:
        patient = user.patient_profile
        all_appts = Appointment.objects.filter(patient=patient).order_by('-appointment_date')
        pending = all_appts.filter(status='PENDING').count()
        approved = all_appts.filter(status='APPROVED').count()
        appointments = all_appts[:5]
        context = {'patient': patient, 'appointments': appointments, 'pending': pending, 'approved': approved}
        return render(request, 'clinic/patient_dashboard.html', context)
    except PatientProfile.DoesNotExist:
        try:
            doctor = user.doctor_profile
            all_appts = Appointment.objects.filter(doctor=doctor).order_by('-appointment_date')
            pending = all_appts.filter(status='PENDING').count()
            appointments = all_appts[:5]
            context = {'doctor': doctor, 'appointments': appointments, 'pending': pending}
            return render(request, 'clinic/doctor_dashboard.html', context)
        except DoctorProfile.DoesNotExist:
            return redirect('home')

@login_required
def book_appointment(request):
    try:
        patient = request.user.patient_profile
    except PatientProfile.DoesNotExist:
        messages.error(request, 'Only patients can book appointments.')
        return redirect('dashboard')
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = patient
            appointment.save()
            messages.success(request, 'Appointment booked successfully! Awaiting approval.')
            return redirect('my_appointments')
    else:
        form = AppointmentForm()
    return render(request, 'clinic/book_appointment.html', {'form': form})

@login_required
def my_appointments(request):
    try:
        patient = request.user.patient_profile
        appointments = Appointment.objects.filter(patient=patient).select_related('doctor__user')
        return render(request, 'clinic/my_appointments.html', {'appointments': appointments})
    except PatientProfile.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

@login_required
def cancel_appointment(request, pk):
    try:
        patient = request.user.patient_profile
        appointment = get_object_or_404(Appointment, pk=pk, patient=patient)
        if appointment.status in ['PENDING', 'APPROVED']:
            appointment.status = 'CANCELLED'
            appointment.save()
            messages.success(request, 'Appointment cancelled successfully.')
        else:
            messages.error(request, 'Cannot cancel this appointment.')
    except PatientProfile.DoesNotExist:
        messages.error(request, 'Access denied.')
    return redirect('my_appointments')

@login_required
def doctor_appointments(request):
    try:
        doctor = request.user.doctor_profile
        status_filter = request.GET.get('status', '')
        appointments = Appointment.objects.filter(doctor=doctor).select_related('patient__user')
        if status_filter:
            appointments = appointments.filter(status=status_filter)
        return render(request, 'clinic/doctor_appointments.html', {'appointments': appointments, 'status_filter': status_filter})
    except DoctorProfile.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

@login_required
def update_appointment(request, pk):
    try:
        doctor = request.user.doctor_profile
        appointment = get_object_or_404(Appointment, pk=pk, doctor=doctor)
        if request.method == 'POST':
            form = AppointmentStatusForm(request.POST, instance=appointment)
            if form.is_valid():
                form.save()
                messages.success(request, 'Appointment status updated.')
                return redirect('doctor_appointments')
        else:
            form = AppointmentStatusForm(instance=appointment)
        return render(request, 'clinic/update_appointment.html', {'form': form, 'appointment': appointment})
    except DoctorProfile.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

def doctors_list(request):
    specialization = request.GET.get('specialization', '')
    doctors = DoctorProfile.objects.select_related('user')
    if specialization:
        doctors = doctors.filter(specialization=specialization)
    schedules = DoctorSchedule.objects.filter(is_available=True).select_related('doctor__user')
    return render(request, 'clinic/doctors.html', {
        'doctors': doctors, 'schedules': schedules,
        'specialization_choices': DoctorProfile.SPECIALIZATION_CHOICES,
        'selected': specialization
    })

@login_required
def medical_history(request):
    try:
        patient = request.user.patient_profile
        records = MedicalRecord.objects.filter(patient=patient).select_related('doctor__user')
        return render(request, 'clinic/medical_history.html', {'records': records, 'patient': patient})
    except PatientProfile.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

@login_required
def add_medical_record(request, appointment_pk=None):
    try:
        doctor = request.user.doctor_profile
    except DoctorProfile.DoesNotExist:
        messages.error(request, 'Only doctors can add records.')
        return redirect('dashboard')
    appointment = None
    if appointment_pk:
        appointment = get_object_or_404(Appointment, pk=appointment_pk, doctor=doctor)
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.doctor = doctor
            if appointment:
                record.appointment = appointment
                appointment.status = 'COMPLETED'
                appointment.save()
            record.save()
            messages.success(request, 'Medical record added successfully.')
            return redirect('doctor_appointments')
    else:
        initial = {}
        if appointment:
            initial['patient'] = appointment.patient
        form = MedicalRecordForm(initial=initial)
    return render(request, 'clinic/add_record.html', {'form': form, 'appointment': appointment})

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your message has been sent. We will get back to you soon!')
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'clinic/contact.html', {'form': form})

@staff_member_required
def admin_dashboard(request):
    total_patients = PatientProfile.objects.count()
    total_doctors = DoctorProfile.objects.count()
    total_appointments = Appointment.objects.count()
    pending_appointments = Appointment.objects.filter(status='PENDING').count()
    recent_appointments = Appointment.objects.select_related('patient__user', 'doctor__user').order_by('-created_at')[:10]
    unread_messages = ContactMessage.objects.filter(is_read=False).count()
    context = {
        'total_patients': total_patients, 'total_doctors': total_doctors,
        'total_appointments': total_appointments, 'pending_appointments': pending_appointments,
        'recent_appointments': recent_appointments, 'unread_messages': unread_messages,
    }
    return render(request, 'clinic/admin_dashboard.html', context)

@staff_member_required
def manage_users(request):
    patients = PatientProfile.objects.select_related('user').all()
    doctors = DoctorProfile.objects.select_related('user').all()
    return render(request, 'clinic/manage_users.html', {'patients': patients, 'doctors': doctors})

@staff_member_required
def admin_messages(request):
    msgs = ContactMessage.objects.all().order_by('-submitted_at')
    ContactMessage.objects.filter(is_read=False).update(is_read=True)
    return render(request, 'clinic/admin_messages.html', {'messages_list': msgs})

@staff_member_required
def all_appointments(request):
    status_filter = request.GET.get('status', '')
    appointments = Appointment.objects.select_related('patient__user', 'doctor__user').all()
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    return render(request, 'clinic/all_appointments.html', {'appointments': appointments, 'status_filter': status_filter})
