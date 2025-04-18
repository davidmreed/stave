# Generated by Django 5.1.4 on 2025-02-13 02:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("stave", "0011_applicationform_close_date_applicationform_closed"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="game",
            name="role_groups",
        ),
        migrations.AlterField(
            model_name="rolegroupcrewassignment",
            name="game",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="role_groups",
                to="stave.game",
            ),
        ),
    ]
