# Generated by Django 5.1.4 on 2025-02-03 00:49

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("stave", "0004_alter_crewassignment_user_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="applicationresponse",
            options={
                "ordering": [
                    "question__application_form",
                    "question__application_form_template",
                    "question__order_key",
                ]
            },
        ),
        migrations.AlterModelOptions(
            name="question",
            options={
                "ordering": [
                    "application_form",
                    "application_form_template",
                    "order_key",
                ]
            },
        ),
        migrations.AddField(
            model_name="question",
            name="order_key",
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]
