# Generated by Django 4.1.7 on 2025-02-13 21:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("centres", "0004_medecintraitant"),
        ("prestations", "0020_prestationlunetterie_prestation"),
    ]

    operations = [
        migrations.AddField(
            model_name="prestationlunetterie",
            name="medecin_traitant",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="centres.medecintraitant",
            ),
        ),
    ]
