from django.contrib import admin
from django.contrib.auth.hashers import make_password
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from .models import AttendanceRecordingTb, UserTb, CourseTb, EnrollmentTb, ActiveQRCode

class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('attdID', 'date', 'time_in', 'time_out', 'classType', 'status', 'userID', 'courseID')
    search_fields = ('attdID', 'date', 'time_in', 'time_out', 'classType', 'status', 'userID', 'courseID')
admin.site.register(AttendanceRecordingTb, AttendanceAdmin)

class AttendanceAdmin1(admin.ModelAdmin):
    list_display = ('userID', 'fName', 'lName', 'email','gender', 'phoneNum', 'macAddress', 'userType')
    search_fields = ('userID', 'fName', 'lName', 'email','gender', 'phoneNum', 'macAddress', 'userType')
    readonly_fields = ('userID',)
    fields = ('fName', 'lName', 'email', 'password', 'gender', 'phoneNum', 'macAddress', 'userType')  # Exclude userID from the form


    def save_model(self, request, obj, form, change):
        if not obj.userID:
            obj.save()  # This will trigger the save() method and assign userID
        # ✅ Hash the password only if it's not already hashed
        if not obj.password.startswith('pbkdf2_sha256$'):  
            obj.password = make_password(obj.password)
        super().save_model(request, obj, form, change)


    actions = ['Enroll_students']

    def Enroll_students(self, request, queryset):
        courses = CourseTb.objects.all()

        # 🟢 Step 1: If submitted from custom form
        if request.method == 'POST' and 'apply' in request.POST:
            selected_course_id = request.POST.get('course')
            student_ids = request.POST.getlist(ACTION_CHECKBOX_NAME)  # ✅ Real key is 'action_checkbox'

            print("✅ POST received from custom form!")
            print("📘 Course:", selected_course_id)
            print("🧍 Students:", student_ids)

            try:
                selected_course = CourseTb.objects.get(courseID=selected_course_id)
            except CourseTb.DoesNotExist:
                self.message_user(request, "❌ Course not found.")
                return HttpResponseRedirect(request.get_full_path())

            count = 0
            for sid in student_ids:
                try:
                    student = UserTb.objects.get(pk=sid)
                    if not EnrollmentTb.objects.filter(userID=student, courseID=selected_course).exists():
                        EnrollmentTb.objects.create(userID=student, courseID=selected_course)
                        count += 1
                except UserTb.DoesNotExist:
                    continue

            self.message_user(request, f"✅ Enrolled {count} students to {selected_course.courseName}")
            return redirect('/admin/attendanceRecordingQR/enrollmenttb/')

        # 🟢 Step 2: First GET request
        return render(request, 'enrollDatabase.html', {
            'students': queryset,
            'courses': courses,
            'action_checkbox_name': ACTION_CHECKBOX_NAME,
        })


admin.site.register(UserTb, AttendanceAdmin1)

class AttendanceAdmin2(admin.ModelAdmin):
    list_display = ('courseID', 'courseName', 'total_classes')
    search_fields = ('courseID', 'courseName', 'total_classes')
admin.site.register(CourseTb, AttendanceAdmin2)

class AttendanceAdmin3(admin.ModelAdmin):
    list_display = ('enrollmentID', 'userID', 'courseID')
    search_fields = ('enrollmentID', 'userID', 'courseID')
admin.site.register(EnrollmentTb, AttendanceAdmin3)


class AttendanceAdmin4(admin.ModelAdmin):
    list_display = ('subject', 'subjectName', 'classType', 'date', 'qr_timestamp')
    search_fields = ('subject', 'subjectName', 'classType', 'date', 'qr_timestamp')
admin.site.register(ActiveQRCode, AttendanceAdmin4)


