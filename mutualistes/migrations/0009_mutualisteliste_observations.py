# Generated by Django 4.1.7 on 2025-02-19 18:53

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mutualistes", "0008_alter_natureprestationsociale_montant"),
    ]

    operations = [
        migrations.AddField(
            model_name="mutualisteliste",
            name="observations",
            field=models.CharField(default="R.A.S", max_length=255),
        ),
    ]
