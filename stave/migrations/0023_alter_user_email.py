# Generated by Django 5.1.4 on 2025-03-17 00:57

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("stave", "0022_remove_applicationform_assigned_email_template_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.CharField(max_length=256),
        ),
    ]
