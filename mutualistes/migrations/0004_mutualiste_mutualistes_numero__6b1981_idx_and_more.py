# Generated by Django 4.1.7 on 2025-01-26 18:54

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mutualistes", "0003_beneficiaire_photo"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="mutualiste",
            index=models.Index(
                fields=["numero_contrat"], name="mutualistes_numero__6b1981_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="mutualiste",
            index=models.Index(
                fields=["code_matricule"], name="mutualistes_code_ma_fa58c2_idx"
            ),
        ),
    ]
