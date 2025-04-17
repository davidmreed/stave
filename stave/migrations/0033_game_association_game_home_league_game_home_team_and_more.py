# Generated by Django 5.1.4 on 2025-04-13 03:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stave', '0032_alter_gametemplate_end_time_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='association',
            field=models.CharField(choices=[('WFTDA', 'WFTDA'), ('JRDA', 'JRDA'), ('MRDA', 'MRDA'), ('Other', 'Other')], default='WFTDA', max_length=32),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='game',
            name='home_league',
            field=models.CharField(default='Unknown', max_length=256),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='game',
            name='home_team',
            field=models.CharField(default='Unknown', max_length=256),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='game',
            name='kind',
            field=models.CharField(choices=[('Champs', 'Champs'), ('Playoff', 'Playoff'), ('Cups', 'Cups'), ('National', 'National'), ('Sanc', 'Sanc'), ('Reg', 'Reg'), ('Other', 'Other')], default='Reg', max_length=32),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='game',
            name='visiting_league',
            field=models.CharField(default='Unknown', max_length=256),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='game',
            name='visiting_team',
            field=models.CharField(default='Unknown', max_length=256),
            preserve_default=False,
        ),
    ]
