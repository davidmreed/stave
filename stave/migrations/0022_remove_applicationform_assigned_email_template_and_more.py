# Generated by Django 5.1.4 on 2025-03-16 23:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("stave", "0021_application_invitation_email_sent_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="applicationform",
            name="assigned_email_template",
        ),
        migrations.RemoveField(
            model_name="applicationform",
            name="confirmed_email_template",
        ),
        migrations.RemoveField(
            model_name="applicationform",
            name="rejected_email_template",
        ),
        migrations.AddField(
            model_name="application",
            name="decline_email_set",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="applicationform",
            name="invitation_email_template",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="application_form_invitation",
                to="stave.messagetemplate",
            ),
        ),
        migrations.AddField(
            model_name="applicationform",
            name="rejection_email_template",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="application_form_rejection",
                to="stave.messagetemplate",
            ),
        ),
        migrations.AddField(
            model_name="applicationform",
            name="schedule_email_template",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="application_form_schedule",
                to="stave.messagetemplate",
            ),
        ),
        migrations.AddField(
            model_name="message",
            name="subject",
            field=models.CharField(default="", max_length=256),
            preserve_default=False,
        ),
    ]
