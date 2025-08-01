# Generated by Django 5.2.3 on 2025-07-26 19:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("stave", "0044_alter_applicationform_application_kind_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="applicationformtemplate",
            name="confirmed_email_template",
        ),
        migrations.AddField(
            model_name="applicationformtemplate",
            name="application_availability_kind",
            field=models.IntegerField(
                choices=[(1, "Entire Event"), (2, "By Day"), (3, "By Game")], default=1
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="applicationformtemplate",
            name="invitation_email_template",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="application_form_templates_invitation",
                to="stave.messagetemplate",
            ),
        ),
        migrations.AddField(
            model_name="messagetemplate",
            name="subject",
            field=models.TextField(default=""),
            preserve_default=False,
        ),
    ]
