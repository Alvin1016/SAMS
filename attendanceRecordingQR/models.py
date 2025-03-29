from django.db import models
from django.utils.timezone import now



class UserTb(models.Model):
    USER_TYPE_CHOICES = [
        ('Staff', 'Staff'),
        ('Student', 'Student')
    ]

    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female')
    ]

    userID = models.IntegerField(primary_key=True, blank=True)
    fName = models.CharField(max_length=255)
    lName = models.CharField(max_length=255)
    email = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    gender = models.CharField(max_length=255, choices=GENDER_CHOICES)
    phoneNum = models.CharField(max_length=255)
    macAddress = models.CharField(max_length=255)
    userType = models.CharField(max_length=255, choices=USER_TYPE_CHOICES)

    def save(self, *args, **kwargs):
        # Only assign userID if it's not already set
        if not self.userID:
            if self.userType == 'Student':
                last_student = UserTb.objects.filter(userType='Student').order_by('-userID').first()
                self.userID = last_student.userID + 1 if last_student else 2213700
            elif self.userType == 'Staff':
                last_staff = UserTb.objects.filter(userType='Staff', userID__gte=1000).order_by('-userID').first()
                self.userID = (last_staff.userID + 1) if last_staff else 1000

        super().save(*args, **kwargs)

        

class CourseTb(models.Model):
    courseID = models.IntegerField(primary_key=True)
    courseName = models.CharField(max_length=255)
    total_classes = models.IntegerField(default=0)

class AttendanceRecordingTb(models.Model):
    attdID = models.AutoField(primary_key=True)
    date = models.DateField()
    time_in = models.TimeField(null=True, blank=True)  # ✅ First scan
    time_out = models.TimeField(null=True, blank=True)  # ✅ Second scan
    classType = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    userID = models.ForeignKey(UserTb, on_delete=models.CASCADE)
    courseID = models.ForeignKey(CourseTb, on_delete=models.CASCADE)
    

class EnrollmentTb(models.Model):
    enrollmentID = models.AutoField(primary_key=True)
    userID = models.ForeignKey(UserTb, on_delete=models.CASCADE)
    courseID = models.ForeignKey(CourseTb, on_delete=models.CASCADE)


class ActiveQRCode(models.Model):
    subject = models.CharField(max_length=100)
    subjectName = models.CharField(max_length=100)
    classType = models.CharField(max_length=50)
    date = models.DateField()
    qr_timestamp = models.DateTimeField(default=now)  # Stores the latest QR timestamp


