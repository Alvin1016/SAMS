from django.core.management.base import BaseCommand
from django.utils.timezone import now
from attendanceRecordingQR.models import AttendanceRecordingTb, EnrollmentTb, CourseTb
from datetime import date

class Command(BaseCommand):
    help = 'Mark students as Absent only if at least one student attended the class that day.'

    def handle(self, *args, **kwargs):
        target_date = date.today()

        # ✅ Find all courses and class types that had at least one attendance recorded
        held_classes = AttendanceRecordingTb.objects.filter(date=target_date).values(
            'courseID', 'classType'
        ).distinct()

        created_count = 0

        for held_class in held_classes:
            course = held_class['courseID']
            class_type = held_class['classType']

            # ✅ Get students enrolled in this course
            enrolled_students = EnrollmentTb.objects.filter(courseID=course)

            for enrollment in enrolled_students:
                student = enrollment.userID

                # ✅ Check if student has attendance record for this course and date
                attendance_exists = AttendanceRecordingTb.objects.filter(
                    date=target_date,
                    userID=student,
                    courseID=course,
                    classType=class_type
                ).exists()
                
                course_instance = CourseTb.objects.get(courseID=course)

                if not attendance_exists:
                    # ✅ If no attendance record, mark as "Absent"
                    AttendanceRecordingTb.objects.create(
                        date=target_date,
                        time_in=None,
                        time_out=None,
                        classType=class_type,
                        status="Absent",
                        userID=student,
                        courseID=course_instance
                    )
                    created_count += 1
                    self.stdout.write(f"📌 Marked Absent: {student} - {course} ({class_type}) on {target_date}")

        self.stdout.write(self.style.SUCCESS(
            f'✅ Successfully created {created_count} Absent records for date {target_date}.'
        ))
