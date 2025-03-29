from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('studentDashboard/', views.studentDashboard, name='studentDashboard'),
    path('attendanceTracking/', views.attendanceTracking, name='attendanceTracking'),
    path('', views.login, name='login'),
    path('profile/', views.profile, name='profile'),
    path('studentProfile/', views.studentProfile, name='studentProfile'),
    path('registration/', views.registration, name='registration'),
    path('report/', views.report, name='report'),
    path('student/', views.student, name='student'),
    path('success/', views.success, name='success'),  
    path('unsuccess/', views.unsuccess, name='unsuccess'),      
    path('get_students/', views.get_students, name='get_students'),
    path('mannual_record_attendance/', views.mannual_record_attendance, name='mannual_record_attendance'),
    path('attendance_capture_mac_address/', views.attendance_capture_mac_address, name='attendance_capture_mac_address'),
    path('attendance_retrieve_mac_address/', views.attendance_retrieve_mac_address, name='attendance_retrieve_mac_address'),
    path('generate_qr_code/', views.generate_qr_code, name='generate_qr_code'),
    path('verify_attendance/', views.verify_attendance, name='verify_attendance'),
    path('get_server_ip/', views.get_server_ip, name='get_server_ip'),
    path('user_login/', views.user_login, name='user_login'),
    path('register_user/', views.register_user, name='register_user'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('otp_page/', views.otp_page, name='otp_page'),
    path('login/', views.user_logout, name='logout'),
    path('get_user_profile/', views.get_user_profile, name='get_user_profile'),
    path('update_user_profile/', views.update_user_profile, name='update_user_profile'),
    path('get_students_by_course/<int:course_id>/', views.get_students_by_course, name='get_students_by_course'),
    path('generate_monthly_report/<int:course_id>/<str:month>/<int:year>/', views.generate_monthly_report, name='generate_monthly_report'),
    path("capture_mac_address/", views.capture_mac_address, name="capture_mac_address"),
    path('retrieve_mac_address/', views.retrieve_mac_address, name='retrieve_mac_address'),
    path('reset_password_request_otp/', views.reset_password_request_otp, name='reset_password_request_otp'),
    path('reset_password_verify_otp/', views.reset_password_verify_otp, name='reset_password_verify_otp'),

    
]

