# Generated by Django 5.1.4 on 2025-04-14 15:36

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("stave", "0033_game_association_game_home_league_game_home_team_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="gametemplate",
            name="association",
            field=models.CharField(
                blank=True,
                choices=[
                    ("WFTDA", "WFTDA"),
                    ("JRDA", "JRDA"),
                    ("MRDA", "MRDA"),
                    ("Other", "Other"),
                ],
                max_length=32,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="gametemplate",
            name="home_league",
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name="gametemplate",
            name="home_team",
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name="gametemplate",
            name="kind",
            field=models.CharField(
                blank=True,
                choices=[
                    ("Champs", "Champs"),
                    ("Playoff", "Playoff"),
                    ("Cups", "Cups"),
                    ("National", "National"),
                    ("Sanc", "Sanc"),
                    ("Reg", "Reg"),
                    ("Other", "Other"),
                ],
                max_length=32,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="gametemplate",
            name="visiting_league",
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name="gametemplate",
            name="visiting_team",
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name="gametemplate",
            name="end_time",
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="gametemplate",
            name="start_time",
            field=models.TimeField(blank=True, null=True),
        ),
    ]
