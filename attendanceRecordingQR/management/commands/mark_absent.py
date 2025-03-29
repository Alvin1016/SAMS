from django.core.management.base import BaseCommand
from django.utils.timezone import now, localtime
from django.utils import timezone
from datetime import datetime, timedelta
from attendanceRecordingQR.models import AttendanceRecordingTb

class Command(BaseCommand):
    help = 'Mark pending attendance records as absent if time_out is not recorded after 5 hours'

    def handle(self, *args, **kwargs):
        current_time = localtime(now())  # ✅ Convert now() to local time
        threshold_seconds = 5 * 60 * 60  # ✅ 5 hours threshold

        # ✅ Only check records where time_in is already in the past
        pending_records = AttendanceRecordingTb.objects.filter(
            status="Pending",
            time_out__isnull=True,
            date__lte=current_time.date()  # ✅ Ensure we only check today and past records
        )

        updated_count = 0
        skipped_count = 0

        for record in pending_records:
            if record.time_in is None:
                self.stdout.write(f"⚠️ Skipped Record {record.attdID}: No time_in value (Possibly missing in DB)")
                skipped_count += 1
                continue

            # ✅ Convert record time to local timezone
            time_in_dt = datetime.combine(record.date, record.time_in)
            time_in_dt = timezone.make_aware(time_in_dt, timezone.get_current_timezone())
            time_in_dt = localtime(time_in_dt)  # ✅ Convert time_in to local time

            # ✅ Ensure current_time is also in local timezone
            current_time = localtime(now())

            # ✅ Only process records where time_in is already in the past
            if time_in_dt > current_time:
                print(now())
                self.stdout.write(f"⚠️ Skipped Record {record.attdID}: Time In is in the future ({time_in_dt})")
                skipped_count += 1
                continue

            # ✅ Calculate time difference
            time_difference = (current_time - time_in_dt).total_seconds()

            # ✅ Debugging logs
            self.stdout.write(f"🕒 Current Time (Local): {current_time}")
            self.stdout.write(f"🕒 Record Time In (Local): {time_in_dt}")
            self.stdout.write(f"🔎 Raw time_in: {record.time_in} | Raw date: {record.date}")
            self.stdout.write(f"⏳ Checking Record {record.attdID}: Time Difference = {time_difference}s, Threshold = {threshold_seconds}s")

            # ✅ If time_in was more than the threshold ago, mark as Absent
            if time_difference > threshold_seconds:
                record.status = "Absent"
                record.save(update_fields=['status'])  # ✅ Ensure only 'status' is updated
                updated_count += 1
                self.stdout.write(f"✅ Updated Record {record.attdID}: Marked as Absent")
            else:
                skipped_count += 1
                self.stdout.write(f"⚠️ Skipped Record {record.attdID}: Only {time_difference}s passed")

        self.stdout.write(self.style.SUCCESS(f"✅ Successfully marked {updated_count} records as Absent. Skipped: {skipped_count}"))
