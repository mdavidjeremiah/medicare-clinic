from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('book/', views.book_appointment, name='book_appointment'),
    path('appointments/', views.my_appointments, name='my_appointments'),
    path('appointments/cancel/<int:pk>/', views.cancel_appointment, name='cancel_appointment'),
    path('doctor/appointments/', views.doctor_appointments, name='doctor_appointments'),
    path('doctor/appointments/update/<int:pk>/', views.update_appointment, name='update_appointment'),
    path('doctor/appointments/record/<int:appointment_pk>/', views.add_medical_record, name='add_medical_record'),
    path('doctor/record/add/', views.add_medical_record, name='add_record'),
    path('doctors/', views.doctors_list, name='doctors'),
    path('history/', views.medical_history, name='medical_history'),
    path('contact/', views.contact, name='contact'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/users/', views.manage_users, name='manage_users'),
    path('admin-dashboard/messages/', views.admin_messages, name='admin_messages'),
    path('admin-dashboard/appointments/', views.all_appointments, name='all_appointments'),
]
