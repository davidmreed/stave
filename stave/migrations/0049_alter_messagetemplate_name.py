# Generated by Django 5.2.3 on 2025-07-28 17:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stave', '0048_messagetemplate_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='messagetemplate',
            name='name',
            field=models.CharField(max_length=256),
        ),
    ]
