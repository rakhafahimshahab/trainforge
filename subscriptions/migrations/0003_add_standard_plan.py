from django.db import migrations, models


def starter_to_free(apps, schema_editor):
    Subscription = apps.get_model("subscriptions", "Subscription")
    Subscription.objects.filter(plan="starter").update(plan="free")
    UpgradeRequest = apps.get_model("subscriptions", "UpgradeRequest")
    UpgradeRequest.objects.filter(requested_plan="starter").update(requested_plan="free")


def free_to_starter(apps, schema_editor):
    Subscription = apps.get_model("subscriptions", "Subscription")
    Subscription.objects.filter(plan="free").update(plan="starter")
    UpgradeRequest = apps.get_model("subscriptions", "UpgradeRequest")
    UpgradeRequest.objects.filter(requested_plan="free").update(requested_plan="starter")


class Migration(migrations.Migration):

    dependencies = [
        ("subscriptions", "0002_upgraderequest"),
    ]

    operations = [
        migrations.RunPython(starter_to_free, reverse_code=free_to_starter),
        migrations.AlterField(
            model_name="subscription",
            name="plan",
            field=models.CharField(
                choices=[("free", "Free"), ("standard", "Standard"), ("pro", "Pro")],
                default="free",
                max_length=24,
            ),
        ),
        migrations.AlterField(
            model_name="upgraderequest",
            name="requested_plan",
            field=models.CharField(
                choices=[("free", "Free"), ("standard", "Standard"), ("pro", "Pro")],
                max_length=24,
            ),
        ),
    ]
