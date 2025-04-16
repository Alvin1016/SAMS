from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password,check_password
import json, re, subprocess, platform, socket, random, pytz
from datetime import datetime
from django.core.cache import cache  
from django.utils import timezone
from django.utils.http import urlencode
from django.views.decorators.cache import cache_control
from django.utils.timezone import localtime,now
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from .models import AttendanceRecordingTb, UserTb, CourseTb, EnrollmentTb, ActiveQRCode
MAC_STORE = {} 


def attendanceTracking(request):
    if 'user_name' not in request.session:
        return redirect('login')
    
    courses = CourseTb.objects.all()
    context = {'courses': courses}
    return render(request, 'attendanceRecord.html', context)

def dashboard(request):
    if 'user_name' not in request.session:
        return redirect('login')
    return render(request, 'dashboard.html')

def studentDashboard(request):
    
    if 'user_name' not in request.session:
        return redirect('login')

    user_id = request.session.get('user_id')

    enrolled_courses = EnrollmentTb.objects.filter(userID=user_id).select_related("courseID")

    students = []
    for enrollment in enrolled_courses:
        course = enrollment.courseID
        attendance_records = AttendanceRecordingTb.objects.filter(
            userID=user_id,
            courseID=course.courseID
        ).values('date', 'classType', 'status', 'time_in', 'time_out')

        total_present = AttendanceRecordingTb.objects.filter(
            userID=user_id,
            courseID=course.courseID,
            status="Present"
        ).count()

        attendance_percentage = (total_present / course.total_classes * 100) if course.total_classes else 0

        students.append({
            'courseName': course.courseName,
            'courseID': course.courseID,
            'attendance': round(attendance_percentage, 2),
            'attendance_records': attendance_records,
        })

    return render(request, 'studentDashboard.html', {'students': students})


def login(request):
    return render(request, 'login.html')

def profile(request):
    if 'user_name' not in request.session:
        return redirect('login')
    return render(request, 'profile.html')

def studentProfile(request):
    if 'user_name' not in request.session:
        return redirect('login')
    return render(request, 'studentProfile.html')

def registration(request):
    return render(request, 'registration.html')

def report(request):
    if 'user_name' not in request.session:
        return redirect('login')
    courses = CourseTb.objects.all()
    context = {'courses': courses}
    return render(request, 'report.html', context)

def student(request):
    if 'user_name' not in request.session:
        return redirect('login')
    courses = CourseTb.objects.all()
    context = {'courses': courses}
    return render(request, 'student.html', context)

def success(request):
    return render(request, 'success.html')

def unsuccess(request):
    return render(request, 'unsuccess.html')


def get_students(request): 
    course_id = request.GET.get('course_id')
    date = request.GET.get('date')
    classType = request.GET.get('classType')


    try:
        # Ensure course_id is valid
        if not course_id or not date:
            return JsonResponse({"error": "Missing course_id"}, status=400)

        # Convert course_id to integer
        course_id = int(course_id)

        # Fetch students for the specific course
        students = EnrollmentTb.objects.filter(courseID_id=course_id).select_related('userID')

         # Fetch attendance records for the selected date
        attendance_records = AttendanceRecordingTb.objects.filter(
            courseID=course_id, 
            date=date, 
            classType=classType
        ).values('userID', 'status')

        # Create a mapping of userID to attendance status
        attendance_map = {record['userID']: record['status'] for record in attendance_records}

        # Convert to a list of dictionaries
        student_list = [
            {
                'name': f"{student.userID.fName} {student.userID.lName}",
                'id': student.userID.userID,
                'macAddress': student.userID.macAddress,  # Ensure MAC is included
                'status': attendance_map.get(student.userID.userID, "Absent")  
            } for student in students
        ]

        return JsonResponse({
            'students': student_list
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)
    


def mannual_record_attendance(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
            student_id = data.get('student_id')
            status = data.get('status', 'Absent')
            classType = data.get('classType')
            date = data.get('date')
            subject = data.get('courseID')

            course = CourseTb.objects.get(courseID=subject) if subject else None
            student = UserTb.objects.get(userID=student_id)


            attendance_record = AttendanceRecordingTb.objects.filter(
                date=date,
                userID=student,
                courseID=course,
                classType=classType
            ).first()


            if attendance_record:
                # ✅ Update existing record
                attendance_record.status = "Present"
                attendance_record.time_in = None  # Reset time_in
                attendance_record.time_out = None  # Reset time_out
                attendance_record.save()
                message = "Attendance Updated to Present"
            else:
                # ✅ If no record exists, create a new one
                AttendanceRecordingTb.objects.create(
                    date=date,
                    time_in=None,
                    time_out=None,
                    classType=classType,
                    status="Present",
                    userID=student,
                    courseID=course,
                )
                message = "New Attendance Recorded"

            return JsonResponse({'success': True, 'message': message})

        except Exception as e:
            print("Error recording attendance:", e)
            return JsonResponse({'success': False, 'message': str(e)})

    elif request.method == "DELETE":
        try:
            data = json.loads(request.body.decode('utf-8'))
            student_id = data.get('student_id')
            date = data.get('date')
            subject = data.get('courseID')
            classType = data.get('classType')

            course = CourseTb.objects.get(courseID=subject) if subject else None
            student = UserTb.objects.get(userID=student_id)

            # Delete the attendance record
            record = AttendanceRecordingTb.objects.filter(
                date=date, userID=student, courseID=course, classType=classType
            ).first()

            if record:
                record.delete()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'message': 'Record not found'})

        except Exception as e:
            print("Error deleting attendance record:", e)
            return JsonResponse({'success': False, 'message': str(e)})

    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    


def attendance_capture_mac_address(request):
    print("📢 capture_mac_address() is being called!")

    client_ip = get_client_ip(request)  # ✅ Get the client's IP address
    print(f"📢 Checking Client IP: {client_ip}")

    if client_ip.startswith("127.") or client_ip == "0.0.0.0":
        return JsonResponse({"error": "Waiting for a real IP"}, status=202)

    print(f"✅ Real IP found: {client_ip}")
    mac_address = get_mac_from_ip(client_ip)  # ✅ Get MAC from IP
    print(f"🔎 Captured MAC: {mac_address}")

    if not mac_address or mac_address == "Unknown":
        return JsonResponse({"macAddress": "MAC Not Found"})

    # ✅ Store in MAC_STORE using client IP instead of session_id
    MAC_STORE[client_ip] = mac_address
    print(f"✅ MAC {mac_address} stored for IP {client_ip}")

    return JsonResponse({"Submitting MAC Address...": mac_address})


def attendance_retrieve_mac_address(request):
    client_ip = get_client_ip(request)  # ✅ Get the client's IP address

    if not client_ip:
        return JsonResponse({"error": "Could not determine IP"}, status=400)

    mac = MAC_STORE.get(client_ip, "MAC Not Found")  # ✅ Retrieve MAC using IP
    return JsonResponse({"macAddress": mac})
    

    

def generate_qr_code(request):
    subject = request.GET.get('subject')
    subjectName = request.GET.get('subjectName')
    classType = request.GET.get('classType')
    date = request.GET.get('date')

    if not subject or not classType or not date:
        return JsonResponse({"error": "Missing required fields"}, status=400)

    # ✅ Delete old QR codes for this subject & date
    ActiveQRCode.objects.filter(subject=subject, subjectName=subjectName, classType=classType, date=date).delete()

    # ✅ Store new QR timestamp in **local time**
    latest_qr = ActiveQRCode.objects.create(
        subject=subject,
        subjectName=subjectName,
        classType=classType,
        date=date,
        qr_timestamp=localtime(now())  # Store as local time instead of UTC
    )

    return JsonResponse({
        "success": True,
        "qr_timestamp": latest_qr.qr_timestamp.isoformat()  # Send local time to frontend
    })     
    
    

def verify_attendance(request):
    subject = request.GET.get('subject')
    class_type = request.GET.get('classType')
    date = request.GET.get('date')
    qr_timestamp = request.GET.get('qr_timestamp')

    if not subject or not class_type or not date or not qr_timestamp:
        params = {
            'subjectID': "Unknown",
            'subjectName': "Unknown",
            'section': "Unknown",
            'date': "Unknown",
            'error': "❌ Missing required parameters. Attendance Failed!"
            }
        return redirect(f"/attendanceRecordingQR/unsuccess/?{urlencode(params)}")
    
    # ✅ Clean timestamp (Ensure it's correctly formatted)
    qr_timestamp = qr_timestamp.replace(" ", "+")  # Convert space to valid timezone format

    # ✅ Try parsing manually
    try:
        frontend_qr_timestamp = datetime.fromisoformat(qr_timestamp)
    except ValueError:
        frontend_qr_timestamp = None

    # ✅ Convert to local time
    if frontend_qr_timestamp:
        frontend_qr_timestamp = frontend_qr_timestamp.astimezone(pytz.timezone("Asia/Kuala_Lumpur"))



    # ✅ 2️⃣ Parse and localize frontend timestamp
    
    print(f"🟡 Raw QR Timestamp from URL: {qr_timestamp}")
    print(f"✅ Parsed Frontend QR Timestamp: {frontend_qr_timestamp}")

    if frontend_qr_timestamp is None:
        params = {
            'subjectID': "Unknown",
            'subjectName': "Unknown",
            'section': "Unknown",
            'date': "Unknown",
            'error': "❌ Invalid QR Code Format!"
            }
        return redirect(f"/attendanceRecordingQR/unsuccess/?{urlencode(params)}")

    # 1️⃣ Capture MAC address
    capture_response = attendance_capture_mac_address(request)
    print("Capture response:", capture_response.content.decode('utf-8'))

    # 2️⃣ Retrieve MAC address using IP (no session ID needed)
    response = attendance_retrieve_mac_address(request)
    data = json.loads(response.content.decode('utf-8'))
    user_mac_address = data.get("macAddress")
    print(f"Detected MAC Address: {user_mac_address}")

    try:
        # 3️⃣ Get student from MAC address
        student = UserTb.objects.get(macAddress=user_mac_address)
        course = CourseTb.objects.get(courseID=subject)


        if not EnrollmentTb.objects.filter(userID=student, courseID=course).exists():
            params = {
                'subjectID': "Unknown",
                'subjectName': "Unknown",
                'section': "Unknown",
                'date': "Unknown",
                'error': "❌ You are not enrolled in this course"
            }
            return redirect(f"/attendanceRecordingQR/unsuccess/?{urlencode(params)}")


        latest_qr = ActiveQRCode.objects.filter(
            subject=subject, classType=class_type, date=date
        ).order_by('-qr_timestamp').first()

        if not latest_qr:
            params = {
                'subjectID': "Unknown",
                'subjectName': "Unknown",
                'section': "Unknown",
                'date': "Unknown",
                'error': "❌ Invalid QR Code!"
                }
            return redirect(f"/attendanceRecordingQR/unsuccess/?{urlencode(params)}")

        latest_qr_timestamp = localtime(latest_qr.qr_timestamp)  # Convert DB timestamp to local time
        print(f"✅ Latest QR Timestamp from DB: {latest_qr_timestamp}")

        time_difference = abs((latest_qr_timestamp - frontend_qr_timestamp).total_seconds())
        print(f"⏳ Time Difference: {time_difference} seconds")

        if time_difference > 10:  # Adjust threshold if needed
            params = {
                'subjectID': "Unknown",
                'subjectName': "Unknown",
                'section': "Unknown",
                'date': "Unknown",
                'error': "❌ Expired QR Code!"
                }
            return redirect(f"/attendanceRecordingQR/unsuccess/?{urlencode(params)}")

        # 4️⃣ Check if THIS student already has a record
        existing_attendance = AttendanceRecordingTb.objects.filter(
            date=date,
            userID=student,  # ✅ Ensure filtering per student!
            courseID=course,
            classType=class_type
        ).first()

        if existing_attendance:
            # 5️⃣ If time_out is empty, update it for THIS student
            if existing_attendance.time_out is None:
                existing_attendance.time_out = datetime.now().time()
                existing_attendance.save()

                # ✅ Calculate duration
                time_in = datetime.combine(datetime.today(), existing_attendance.time_in)
                time_out = datetime.combine(datetime.today(), existing_attendance.time_out)
                duration = (time_out - time_in).total_seconds() / 60.0

                # ✅ Mark Absent if less than 2 minutes
                existing_attendance.status = "Absent" if duration < 0.1 else "Present"
                existing_attendance.save()

                # ✅ Redirect success
                params = {
                    'subjectID': course.courseID,
                    'subjectName': course.courseName,
                    'section': class_type,
                    'date': date,
                    'timeIn': existing_attendance.time_in.strftime("%I:%M %p"),
                    'timeOut': existing_attendance.time_out.strftime("%I:%M %p"),
                    'studentID': student.userID  # ✅ Add Student ID in response
                }
                return redirect(f"/attendanceRecordingQR/success/?{urlencode(params)}")

            else:
                # ✅ If already marked, just return success page
                params = {
                    'subjectID': course.courseID,
                    'subjectName': course.courseName,
                    'section': class_type,
                    'date': date,
                    'timeIn': existing_attendance.time_in.strftime("%I:%M %p"),
                    'timeOut': existing_attendance.time_out.strftime("%I:%M %p"),
                    'studentID': student.userID  # ✅ Add Student ID in response
                }
                return redirect(f"/attendanceRecordingQR/success/?{urlencode(params)}")

        # 6️⃣ If no existing record for THIS student, create a new one
        new_record = AttendanceRecordingTb.objects.create(
            date=date,
            time_in=datetime.now().time(),
            time_out=None,
            classType=class_type,
            status="Pending",
            userID=student,  # ✅ Ensure unique per student!
            courseID=course,
        )

        # ✅ Redirect success
        params = {
            'subjectID': course.courseID,
            'subjectName': course.courseName,
            'section': class_type,
            'date': date,
            'timeIn': new_record.time_in.strftime("%I:%M %p"),
            'studentID': student.userID  # ✅ Add Student ID in response
        }
        return redirect(f"/attendanceRecordingQR/success/?{urlencode(params)}")

    except UserTb.DoesNotExist:
        params = {
                    'subjectID': "Unknown",
                    'subjectName': "Unknown",
                    'section': "Unknown",
                    'date': "Unknown",
                    'error': "❌ Device Not Registered. Attendance Failed!"
                }
        return redirect(f"/attendanceRecordingQR/unsuccess/?{urlencode(params)}")

    except CourseTb.DoesNotExist:
        params = {
            'subjectID': subject,
            'subjectName': "Unknown",
            'section': class_type,
            'date': date,
            'error': "❌ Course Not Found. Attendance Failed!"
        }
        return redirect(f"/attendanceRecordingQR/unsuccess/?{urlencode(params)}")








def get_server_ip(request):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))  # Google DNS (Gets local network IP)
    ip = s.getsockname()[0]
    s.close()
    return JsonResponse({"server_ip": ip})


@csrf_exempt
def user_login(request):
    if request.method == 'POST': 
        try:
            data = json.loads(request.body)
            user_type = data.get('userType')
            userId_or_email = data.get("userIdOrEmail")
            password = data.get('password')

            print(f"🔍 Login Attempt - UserType: {user_type}, Username/Email: {userId_or_email}")

            # ✅ Validate input
            if not userId_or_email or not password or not user_type:
                return JsonResponse({"success": False, "message": "Missing fields"}, status=400)
            
            # ✅ Check if input is userID or email
            if userId_or_email.isdigit():
                user = UserTb.objects.filter(userID=userId_or_email, userType=user_type).first()
            else:
                user = UserTb.objects.filter(email__iexact=userId_or_email, userType=user_type).first()  # 🔥 Fix Case Sensitivity
            
            if user and check_password(password, user.password):
                request.session['user_id'] = user.userID
                request.session['user_name'] = f"{user.fName} {user.lName}"
                request.session['user_email'] = user.email

                # ✅ Generate OTP
                otp = random.randint(100000, 999999)  # 6-digit OTP
                otp_key = f"otp_{user.email.lower()}"  # 🔥 Use lowercase email for consistency

                # 🔍 Debugging: Print OTP before storing
                print(f"✅ Storing OTP: {otp} in key: {otp_key}")

                cache.set(otp_key, otp, timeout=600)  # ✅ Store OTP for 10 minutes

                # ✅ Send HTML styled OTP Email
                subject = "🔐 Your OTP for Login - SAMS"
                html_content = f"""
                <html>
                <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 30px;">
                    <div style="max-width: 500px; margin: auto; background: white; border-radius: 10px; padding: 30px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                        <h2 style="color: #1877f2;">Hello {user.fName},</h2>
                        <p style="font-size: 16px;">Your OTP for login is:</p>
                        <p style="font-size: 28px; font-weight: bold; color: #333; letter-spacing: 3px;">{otp}</p>
                        <p style="margin-top: 20px; color: #888;">Please do not share this code with anyone.</p>
                    </div>
                </body>
                </html>
                """
                text_content = strip_tags(html_content)

                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email="alvin10381@gmail.com",
                    to=[user.email],
                )
                email.attach_alternative(html_content, "text/html")
                email.send()

                return JsonResponse({
                    "success": True,
                    "message": "OTP sent to your email. Please verify.",
                    "redirectUrl": "/attendanceRecordingQR/otp_page/",
                    "userId": user.userID  
                })
            else:
                return JsonResponse({"success": False, "message": "Invalid credentials"}, status=401)

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)
    
    return JsonResponse({"success": False, "message": "Invalid request method"}, status=405)



@csrf_exempt
def verify_otp(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            userId_or_email = data.get("userIdOrEmail")
            otp_entered = data.get('otp')

            print(f"🔍 Received userID from frontend: {userId_or_email}")  # ✅ Debugging
            print(f"🔍 OTP entered: {otp_entered}")  # ✅ Debugging

            # ✅ Ensure user exists
            if userId_or_email.isdigit():
                user = UserTb.objects.filter(userID=userId_or_email).first()
            else:
                user = UserTb.objects.filter(email=userId_or_email).first()  # 🔥 Fix Case Sensitivity

            if not user:
                print("❌ User not found in database!")  # ✅ Debugging
                return JsonResponse({"success": False, "message": "User not found"}, status=404)

            # ✅ Ensure email case consistency
            otp_key = f"otp_{user.email.lower()}"  # 🔥 Use lowercase email to avoid key mismatch

            # ✅ Get OTP from cache
            otp_stored = cache.get(otp_key)

            # 🔍 Debugging: Print stored OTP before checking
            print(f"🔍 Retrieving OTP from key: {otp_key}, Stored OTP: {otp_stored}")

            if otp_stored and str(otp_entered) == str(otp_stored):
                cache.delete(otp_key)  # ✅ OTP is valid, remove from cache

                # 🎯 **Redirect Based on `userType`**
                if user.userType == 'Student':
                    redirect_url = "/attendanceRecordingQR/studentDashboard/"
                elif user.userType == 'Staff':
                    redirect_url = "/attendanceRecordingQR/dashboard/"
                else:
                    redirect_url = "/attendanceRecordingQR/"  # Default fallback

                return JsonResponse({"success": True, "redirectUrl": redirect_url})
            else:
                print(f"❌ OTP Mismatch! Entered: {otp_entered}, Stored: {otp_stored}")  # ✅ Debugging
                return JsonResponse({"success": False, "message": "Invalid OTP. Please try again."}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)

    return JsonResponse({"success": False, "message": "Invalid request method"}, status=405)



@csrf_exempt
def register_user(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            firstName = data.get('firstName')
            lastName = data.get('lastName')
            gender = data.get('gender')
            phNumber = data.get('phNumber')
            email = data.get('email')
            password = data.get('password')

            # Basic validations
            if not all([firstName, lastName, gender, phNumber, email, password]):
                return JsonResponse({"success": False, "message": "Missing required fields"}, status=400)
            
            # ✅ Check if gender is valid
            if gender not in ['Male', 'Female']:
                return JsonResponse({"success": False, "message": "Invalid gender selection"}, status=400)

            # Optionally check if user already exists
            if UserTb.objects.filter(email=email).exists():
                return JsonResponse({"success": False, "message": "Email already exists"}, status=400)

            # Save user

            hashed_password = make_password(password)

            user = UserTb.objects.create(
                fName=firstName,
                lName=lastName,
                gender=gender,
                phoneNum=phNumber,
                email=email,
                password=hashed_password,  # For real usage, hash the password.
                userType="Student"
            )

            user_id = user.userID

            subject = "🎉 Welcome to SAMS - Your Account Details"

            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 30px;">
                <div style="max-width: 600px; margin: auto; background: #fff; border-radius: 10px; padding: 30px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #1877f2;">Hello {firstName},</h2>
                    <p style="font-size: 16px;">🎓 Welcome to <strong>SAMS</strong>! Your registration was successful.</p>
                    <p style="font-size: 16px;"><strong>Your User ID:</strong> <span style="color: #333; font-size: 18px;">{user_id}</span></p>

                    <p style="margin-top: 20px;">✅ Please keep this User ID safe – you’ll need it to log in.</p>
                    <p style="margin-top: 10px;">🛠️ After logging in, make sure to <strong>update your profile</strong> by adding your MAC address before marking attendance.</p>

                    <hr style="margin: 30px 0;">

                    <p style="font-size: 14px; color: #777;">Best regards,<br><strong>SAMS Team</strong></p>
                </div>
            </body>
            </html>
            """

            text_content = strip_tags(html_content)

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email="alvin10381@gmail.com",
                to=[email],
            )
            email.attach_alternative(html_content, "text/html")
            email.send()

            return JsonResponse({"success": True, "message": "Registration successful"})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)

    return JsonResponse({"success": False, "message": "Invalid request method"}, status=405)




def otp_page(request):
    return render(request, "otp_page.html")  # Render OTP page


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def your_protected_view(request):
    if 'user_name' not in request.session:
        return render(request, 'login.html')  # or redirect

def user_logout(request):
    request.session.flush()  # Clears all session data
    return render(request,"login.html")  # Redirects to the login page
    

def get_user_profile(request):
    """Retrieve user profile based on session user_id."""
    user_id = request.session.get('user_id')  # Get user_id from session

    if not user_id:
        return JsonResponse({"success": False, "message": "User not logged in"}, status=401)

    user = get_object_or_404(UserTb, userID=user_id)  # Get user details

    # Return user data as JSON response
    return JsonResponse({
        "success": True,
        "user": {
            "userID": user.userID,
            "firstName": user.fName,
            "lastName": user.lName,
            "gender": user.gender,
            "email": user.email,
            "phoneNumber": user.phoneNum,
            "macAddress": user.macAddress
        }
    })    

@csrf_exempt
def update_user_profile(request):
    """Update user profile information."""
    if request.method == "POST":
        data = json.loads(request.body)
        user_id = request.session.get('user_id')  # Get user ID from session

        if not user_id:
            return JsonResponse({"success": False, "message": "User not logged in"}, status=401)

        user = get_object_or_404(UserTb, userID=user_id)  # Get user record

        # Update general profile fields
        user.fName = data.get("firstName", user.fName)
        user.lName = data.get("lastName", user.lName)
        user.gender = data.get("gender", user.gender)
        user.email = data.get("email", user.email)
        user.phoneNum = data.get("phoneNumber", user.phoneNum)
        user.macAddress = data.get("macAddress", user.macAddress)

        # ✅ Handle password update (only if user wants to change password)
        if data.get("newPassword") or data.get("currentPassword") or data.get("confirmPassword"):  
            
            # ✅ Ensure all three password fields are provided
            if not all([data.get("newPassword"), data.get("currentPassword"), data.get("confirmPassword")]):
                return JsonResponse({"success": False, "message": "All password fields are required to update password"}, status=400)

            # ✅ Ensure the current password is correct
            if not check_password(data["currentPassword"], user.password):
                return JsonResponse({"success": False, "message": "Current password incorrect"}, status=400)

            # ✅ Ensure new password and confirm password match
            if data["newPassword"] != data["confirmPassword"]:
                return JsonResponse({"success": False, "message": "New password and confirm password do not match"}, status=400)

            # ✅ Hash and update the password
            user.password = make_password(data["newPassword"])
            password_updated = True
        else:
            password_updated = False

        # ✅ Save all user changes (including password)
        user.save()

        # ✅ Return the correct success message
        if password_updated:
            return JsonResponse({"success": True, "message": "Profile and password updated successfully"})
        else:
            return JsonResponse({"success": True, "message": "Profile updated successfully"})

    return JsonResponse({"success": False, "message": "Invalid request method"}, status=405)


def get_students_by_course(request, course_id):
    """Fetch students enrolled in a specific course along with attendance percentage."""
    
    # course_id = request.GET.get('course_id')


    if not course_id:
        return JsonResponse({"success": False, "message": "Missing course ID"}, status=400)

    # 🔹 Get all students enrolled in the selected course
    students = (
        EnrollmentTb.objects.filter(courseID=course_id)
        .select_related("userID")
        .values("userID__userID", "userID__fName", "userID__lName", "courseID__courseName")
    )

    # 🔹 Get total number of classes held for the course
    try:
        course = CourseTb.objects.get(pk=course_id)
        total_classes = course.total_classes
    except CourseTb.DoesNotExist:
        return JsonResponse({"success": False, "message": "Course not found"}, status=404)

    # 🔹 Prepare student list with attendance percentage
    students_list = []
    for student in students:
        student_id = student["userID__userID"]

        # 🔹 Count how many times this student was present
        total_present = AttendanceRecordingTb.objects.filter(
            courseID=course_id, userID=student_id, status="Present"
        ).count()

        # 🔹 Calculate attendance percentage (avoid division by zero)
        attendance_percentage = (total_present / total_classes * 100) if total_classes else 0

        students_list.append({
            "id": student_id,
            "name": f"{student['userID__fName']} {student['userID__lName']}",
            "course": student["courseID__courseName"],
            "attendance": round(attendance_percentage, 2)  # Round to 2 decimal places
        })

    return JsonResponse({"success": True, "students": students_list})


def generate_monthly_report(request, course_id, month, year):
    """Generate a monthly attendance report for a course."""
    
    if not all([course_id, month, year]):
        return JsonResponse({"success": False, "message": "Missing parameters"}, status=400)

    # Convert month name to number (January = 1, February = 2, ...)
    month_number = datetime.strptime(month, "%B").month

    # 🔹 Get total classes held in the month
    course = CourseTb.objects.get(pk=course_id)
    total_classes = course.total_classes

    # 🔹 Get enrolled students for the course
    students = (
        EnrollmentTb.objects.filter(courseID=course_id)
        .select_related("userID")
        .values("userID__userID", "userID__fName", "userID__lName")
    )

    student_report = []
    for student in students:
        student_id = student["userID__userID"]

        # 🔹 Count student attendance
        total_present = AttendanceRecordingTb.objects.filter(
            courseID=course_id, userID=student_id, date__year=year, date__month=month_number, status="Present"
        ).count()

        # 🔹 Calculate attendance percentage
        attendance_percentage = (total_present / total_classes * 100) if total_classes > 0 else 0

        student_report.append({
            "id": student_id,
            "name": f"{student['userID__fName']} {student['userID__lName']}",
            "present": total_present,
            "total_classes": total_classes,
            "attendance": round(attendance_percentage, 2),
            "status": "Bad" if attendance_percentage < 80 else "Good"
        })

    return JsonResponse({"success": True, "report": student_report})



# ✅ Function to Get MAC Address from IP
def get_mac_from_ip(ip):
    try:
        print(f"🔍 Checking MAC for IP: {ip}")

        # ✅ Refresh ARP cache (Send a ping)
        if platform.system().lower() == "windows":
            subprocess.run(["ping", "-n", "1", ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(["ping", "-c", "1", ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # ✅ Get ARP table
        if platform.system().lower() == "windows":
            output = subprocess.check_output(["arp", "-a"], universal_newlines=True)
        else:
            output = subprocess.check_output(["arp", "-n"], universal_newlines=True)

        print(f"📝 ARP Output:\n{output}")  # Debugging

        # 🔎 Extract MAC address using regex (Improved Regex for Better Matching)
        match = re.search(rf"{re.escape(ip)}\s+([0-9A-Fa-f:-]{{17}})", output)
        if match:
            mac = match.group(1)
            print(f"✅ Found MAC Address: {mac}")
            return mac
        else:
            print("❌ MAC Address Not Found in ARP Cache")
            return "Unknown"

    except Exception as e:
        print(f"⚠️ Error getting MAC: {e}")
        return "Unknown"


# ✅ Function to Get Client IP Address
def get_client_ip(request):
    """ Retrieves the real client IP, even if behind a proxy. """
    try:
        "🔍 First, check if IP is passed via proxy headers (Nginx, Apache, Cloudflare)"
        forwarded_ip = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded_ip:
            ip = forwarded_ip.split(",")[0].strip()  # Get the first IP in the list
            if ip and not ip.startswith("127.") and ip != "0.0.0.0":
                print(f"🌍 Found Forwarded IP: {ip}")
                return ip  # ✅ Always return valid external IP

        # 🔥 Otherwise, get the direct remote address
        ip = request.META.get("REMOTE_ADDR", "")
        if ip:
            print(f"🌍 Direct Client IP Detected: {ip}")
            return ip

        # 🚨 Debugging: Log if no IP is found
        print("⚠️ Warning: No Client IP Found in Request Headers!")

    except Exception as e:
        print(f"⚠️ Error retrieving client IP: {e}")

    return "0.0.0.0"  # 🚨 Return a default instead of `None` to avoid breaking logic



def capture_mac_address(request):
    print("📢 capture_mac_address() is being called!")
    session_id = request.GET.get("session")
    if not session_id:
        return JsonResponse({"error": "Session ID required"}, status=400)

    # 1️⃣ Already stored?
    if session_id in MAC_STORE:
        # If the MAC is already captured, return it immediately
        return JsonResponse({"macAddress": MAC_STORE[session_id]})

    client_ip = get_client_ip(request)
    print(f"📢 Checking Client IP: {client_ip}")

    if client_ip.startswith("127.") or client_ip == "0.0.0.0":
        return JsonResponse({"error": "Waiting for a real IP"}, status=202)

    print(f"✅ Real IP found: {client_ip}")
    mac_address = get_mac_from_ip(client_ip)
    print(f"🔎 Captured MAC: {mac_address}")

    # 2️⃣ Store in MAC_STORE
    if mac_address and mac_address == "Unknown":
        return JsonResponse({"macAddress": "MAC Not Found"})
       
    
    if UserTb.objects.filter(macAddress=mac_address).exists():
        return JsonResponse({"Attention": "This MAC address is already registered!"}, status=409)
    
    
    MAC_STORE[session_id] = mac_address
    print(f"✅ MAC {mac_address} stored for session {session_id}")
    print(f"✅ MAC {mac_address} stored in the database")
    return JsonResponse({"Submitting MAC Address...": mac_address})
        


def retrieve_mac_address(request):
    session_id = request.GET.get("session")
    if not session_id:
        return JsonResponse({"error": "Session ID required"}, status=400)
    
    mac = MAC_STORE.get(session_id, "MAC Not Found")
    return JsonResponse({"macAddress": mac})



def reset_password_request_otp(request):
    if request.method == 'GET':
        return render(request, 'reset_password_request_otp.html')

    elif request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        identifier = data.get('identifier', '').strip()

        # Find user by userID or email
        user = None
        if identifier.isdigit():
            user = UserTb.objects.filter(userID=int(identifier)).first()

        if not user:
            user = UserTb.objects.filter(email=identifier).first()

        if not user:
            return JsonResponse({
                'success': False,
                'message': 'No user found with that identifier.'
            })

        # Generate a 6-digit numeric OTP
        otp_code = str(random.randint(100000, 999999))
        
        request.session['reset_otp'] = otp_code
        request.session['reset_identifier'] = identifier
        # Optionally store a timestamp for expiration checks
        request.session['reset_otp_time'] = str(timezone.now())

        # Email the OTP
        try:
            subject = "🔐 Password Reset OTP - SAMS"

            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background-color: #f2f2f2; padding: 30px;">
                <div style="max-width: 600px; margin: auto; background: #fff; border-radius: 10px; padding: 30px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                    <h2 style="color: #1877f2;">Hello {user.fName},</h2>

                    <p style="font-size: 16px;">You’ve requested to reset your SAMS account password.</p>

                    <p style="font-size: 16px;">🔐 <strong>Your OTP code is:</strong></p>
                    <div style="font-size: 28px; font-weight: bold; letter-spacing: 5px; color: #333; margin: 20px 0;">{otp_code}</div>

                    <p style="font-size: 14px; color: #666;">Use this code immediately in the <strong>same browser session</strong>.</p>
                    <p style="font-size: 14px; color: #666;">If you didn’t request this, you can ignore this email.</p>

                    <hr style="margin: 30px 0;">
                    <p style="font-size: 13px; color: #999;">Best regards,<br>SAMS Security Team</p>
                </div>
            </body>
            </html>
            """

            text_content = strip_tags(html_content)

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email="alvin10381@gmail.com",
                to=[user.email],
            )
            email.attach_alternative(html_content, "text/html")
            email.send()

        except Exception as e:
            print("Error sending OTP email:", e)
            return JsonResponse({
                'success': False,
                'message': 'Unable to send OTP. Please try again.'
            })

        return JsonResponse({
            'success': True,
            'message': 'OTP sent to your email. Please check your inbox.'
        })


def reset_password_verify_otp(request):
    if request.method == 'GET':
        return render(request, 'reset_password_verify_otp.html')

    elif request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        identifier = data.get('identifier', '').strip()
        otp_code = data.get('otp_code', '').strip()
        new_password = data.get('new_password', '').strip()

        # Retrieve the stored OTP and identifier from session
        session_otp = request.session.get('reset_otp')
        session_identifier = request.session.get('reset_identifier')
        session_time_str = request.session.get('reset_otp_time')

        if not session_otp or not session_identifier:
            return JsonResponse({
                'success': False,
                'message': 'No OTP found in session or session expired.'
            })
        
        session_time = datetime.fromisoformat(session_time_str)
        if (timezone.now() - session_time).total_seconds() > 600:
            return JsonResponse({
                'success': False,
                'message': 'OTP expired. Please request a new one.'
            })

        # Check if the identifier matches the one used when requesting the OTP
        if session_identifier != identifier:
            return JsonResponse({
                'success': False,
                'message': 'Identifier mismatch. Please request a new OTP.'
            })

        # Compare OTP codes
        if session_otp != otp_code:
            return JsonResponse({
                'success': False,
                'message': 'Invalid OTP code.'
            })

        user = None
        if identifier.isdigit():
            user = UserTb.objects.filter(userID=int(identifier)).first()
        if not user:
            user = UserTb.objects.filter(email=identifier).first()

        if not user:
            return JsonResponse({
                'success': False,
                'message': 'No user found with that identifier.'
            })

        # Set the new password
        user.password = make_password(new_password)
        user.save()

        # Clear session data so it can’t be reused
        request.session.pop('reset_otp', None)
        request.session.pop('reset_identifier', None)
        request.session.pop('reset_otp_time', None)

        return JsonResponse({
            'success': True,
            'message': 'Password updated successfully!'
        })