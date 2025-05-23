# Generated by Django 5.1.4 on 2025-04-10 14:00

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("stave", "0030_user_is_staff"),
    ]

    operations = [
        migrations.AlterField(
            model_name="rolegroupcrewassignment",
            name="crew_overrides",
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="role_group_override_assignments",
                to="stave.crew",
            ),
        ),
    ]
