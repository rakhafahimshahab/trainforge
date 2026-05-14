from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Profile, TrainerAccount
from appointments.models import Appointment
from clients.models import Client
from exercises.models import Exercise
from plans.models import TrainingPlan, TrainingPlanExercise
from progress.models import ProgressLog
from subscriptions.models import Subscription

User = get_user_model()

class Command(BaseCommand):
    help = "Seed the database with demo trainer, admin, and sample data."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Seeding TrainForge demo data…"))

        trainer_user = self._ensure_user(
            email="trainer@example.com",
            password="Trainer123!",
            full_name="Riley Chen",
            role=Profile.ROLE_TRAINER,
        )
        admin_user = self._ensure_user(
            email="admin@example.com",
            password="Admin1234!",
            full_name="Platform Admin",
            role=Profile.ROLE_ADMIN,
            is_staff=True,
            is_superuser=True,
        )

        trainer_account = trainer_user.trainer_account
        trainer_account.business_name = "Forge Fitness"
        trainer_account.save(update_fields=["business_name"])

        clients_data = [
            {
                "full_name": "Sarah Lee",
                "email": "sarah.lee@example.com",
                "phone": "0411 222 333",
                "fitness_goal": "Strength + fat loss",
                "preferred_times": "Mon / Wed / Fri",
                "notes": "Mild knee discomfort",
                "status": Client.STATUS_ACTIVE,
            },
            {
                "full_name": "Daniel Wong",
                "email": "daniel.wong@example.com",
                "phone": "0411 444 555",
                "fitness_goal": "Build muscle, hypertrophy focus",
                "preferred_times": "Tue / Thu evenings",
                "notes": "",
                "status": Client.STATUS_ACTIVE,
            },
            {
                "full_name": "Ava Nguyen",
                "email": "ava.nguyen@example.com",
                "phone": "0411 666 777",
                "fitness_goal": "General fitness, return to running",
                "preferred_times": "Wed / Sat mornings",
                "notes": "Pregnant - second trimester. Avoid prone work.",
                "status": Client.STATUS_ACTIVE,
            },
        ]
        clients = {}
        for data in clients_data:
            obj, _ = Client.objects.update_or_create(
                trainer_account=trainer_account,
                full_name=data["full_name"],
                defaults={**data, "trainer_account": trainer_account},
            )
            clients[data["full_name"]] = obj

        exercises_data = [
            ("Goblet Squat", "lower_body", 3, 10, "Hold a kettlebell at chest, squat to depth."),
            ("Dumbbell Bench Press", "upper_body", 3, 8, "Controlled tempo, full ROM."),
            ("Lat Pulldown", "back", 3, 12, "Lead with elbows, avoid leaning back."),
            ("Romanian Deadlift", "lower_body", 3, 10, "Hinge at hips, neutral spine."),
            ("Step Ups", "lower_body", 3, 12, "Drive through the heel."),
            ("Seated Shoulder Press", "upper_body", 3, 10, "Brace core, full lockout."),
            ("Plank", "core", 3, 30, "Hold 30 sec per set."),
            ("Treadmill Warm-up", "cardio", 1, 5, "5-minute easy pace."),
        ]
        exercises = {}
        for name, category, sets, reps, description in exercises_data:
            obj, _ = Exercise.objects.update_or_create(
                trainer_account=trainer_account,
                name=name,
                defaults={
                    "trainer_account": trainer_account,
                    "category": category,
                    "default_sets": sets,
                    "default_reps": reps,
                    "description": description,
                },
            )
            exercises[name] = obj

        plan, _ = TrainingPlan.objects.update_or_create(
            trainer_account=trainer_account,
            client=clients["Sarah Lee"],
            title="Sarah 3-Day Strength Plan",
            defaults={
                "goal_summary": "Beginner-friendly progression mixing compound lifts with core work.",
                "status": TrainingPlan.STATUS_ACTIVE,
            },
        )
        plan.plan_exercises.all().delete()
        plan_exercise_specs = [
            ("Goblet Squat", 3, 10, "Keep chest up"),
            ("Dumbbell Bench Press", 3, 8, "Controlled tempo"),
            ("Lat Pulldown", 3, 12, "Pause at the bottom"),
            ("Plank", 3, 30, "30s holds"),
        ]
        for order, (name, sets, reps, notes) in enumerate(plan_exercise_specs, start=1):
            TrainingPlanExercise.objects.create(
                plan=plan,
                exercise=exercises[name],
                exercise_order=order,
                sets=sets,
                reps=reps,
                notes=notes,
            )

        Appointment.objects.filter(trainer_account=trainer_account).delete()
        today = timezone.localdate()
        monday = today - timedelta(days=today.weekday())
        tz = timezone.get_current_timezone()
        appt_specs = [
            (0, time(8, 0),  time(9, 0),  "Sarah Lee",   Appointment.SESSION_TRAINING,      Appointment.STATUS_COMPLETED),
            (1, time(10, 0), time(10, 30),"Sarah Lee",   Appointment.SESSION_CHECKIN,       Appointment.STATUS_SCHEDULED),
            (1, time(18, 0), time(19, 0), "Daniel Wong", Appointment.SESSION_TRAINING,      Appointment.STATUS_SCHEDULED),
            (2, time(8, 30), time(9, 0),  "Ava Nguyen",  Appointment.SESSION_CONSULTATION,  Appointment.STATUS_SCHEDULED),
            (2, time(13, 0), time(14, 0), "Daniel Wong", Appointment.SESSION_TRAINING,      Appointment.STATUS_SCHEDULED),
            (3, time(10, 0), time(11, 0), "Ava Nguyen",  Appointment.SESSION_TRAINING,      Appointment.STATUS_SCHEDULED),
            (4, time(8, 0),  time(9, 0),  "Daniel Wong", Appointment.SESSION_TRAINING,      Appointment.STATUS_SCHEDULED),
            (4, time(18, 0), time(19, 0), "Sarah Lee",   Appointment.SESSION_TRAINING,      Appointment.STATUS_SCHEDULED),
            (0, time(16, 0), time(17, 0), "Ava Nguyen",  Appointment.SESSION_TRAINING,      Appointment.STATUS_CANCELLED),
        ]
        for day_offset, start_t, end_t, client_name, session_type, status in appt_specs:
            day = monday + timedelta(days=day_offset)
            start_dt = timezone.make_aware(datetime.combine(day, start_t), tz)
            end_dt = timezone.make_aware(datetime.combine(day, end_t), tz)
            Appointment.objects.create(
                trainer_account=trainer_account,
                client=clients[client_name],
                session_type=session_type,
                start_at=start_dt,
                end_at=end_dt,
                status=status,
                notes="",
            )

        ProgressLog.objects.filter(trainer_account=trainer_account, client=clients["Sarah Lee"]).delete()
        log_data = [
            (date(2026, 4, 5),  "Lat Pulldown",        3, 12, Decimal("35.00"), "Stable performance"),
            (date(2026, 4, 8),  "Dumbbell Bench Press", 3,  8, Decimal("14.00"), "Increase next week"),
            (date(2026, 4, 10), "Goblet Squat",         3, 10, Decimal("18.00"), "Form improved"),
            (date(2026, 4, 15), "Goblet Squat",         3, 10, Decimal("20.00"), "Bumped weight"),
            (date(2026, 4, 17), "Dumbbell Bench Press", 3,  8, Decimal("16.00"), ""),
            (date(2026, 4, 22), "Lat Pulldown",        3, 12, Decimal("38.00"), ""),
            (date(2026, 4, 24), "Goblet Squat",         3, 10, Decimal("22.00"), "Strong session"),
            (date(2026, 4, 29), "Dumbbell Bench Press", 3,  8, Decimal("18.00"), ""),
        ]
        for log_date, exercise_name, sets, reps, weight, notes in log_data:
            ProgressLog.objects.create(
                trainer_account=trainer_account,
                client=clients["Sarah Lee"],
                exercise=exercises[exercise_name],
                log_date=log_date,
                actual_sets=sets,
                actual_reps=reps,
                actual_weight_kg=weight,
                notes=notes,
            )

        Subscription.objects.filter(trainer_account=trainer_account).delete()
        Subscription.objects.create(
            trainer_account=trainer_account,
            plan=Subscription.PLAN_FREE,
            start_date=date(2026, 1, 1),
            end_date=date(2036, 12, 31),
        )

        admin_ta = TrainerAccount.objects.filter(owner=admin_user).first()
        if admin_ta:
            admin_ta.subscriptions.all().delete()
            admin_ta.delete()

        legacy_emails = ["sam@example.com", "jordan@example.com", "casey@example.com", "morgan@example.com"]
        legacy_users = list(User.objects.filter(email__in=legacy_emails))
        for u in legacy_users:
            u.delete()
        if legacy_users:
            self.stdout.write(self.style.WARNING(f"  Removed {len(legacy_users)} legacy demo trainer(s)."))

        self.stdout.write(self.style.SUCCESS("Seed complete."))
        self.stdout.write(self.style.HTTP_INFO("  Trainer login: trainer@example.com / Trainer123!"))
        self.stdout.write(self.style.HTTP_INFO("  Admin login:   admin@example.com / Admin1234!"))

    def _ensure_user(self, *, email, password, full_name, role, is_staff=False, is_superuser=False):
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email,
                "first_name": full_name.split()[0],
                "last_name": " ".join(full_name.split()[1:]),
                "is_staff": is_staff,
                "is_superuser": is_superuser,
            },
        )
        if created or not user.has_usable_password():
            user.set_password(password)
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.save()
        profile, _ = Profile.objects.get_or_create(user=user, defaults={"role": role, "full_name": full_name})
        profile.role = role
        profile.full_name = full_name
        profile.save()
        return user
