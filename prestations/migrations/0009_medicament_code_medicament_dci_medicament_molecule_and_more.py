# Generated by Django 4.1.7 on 2025-02-05 21:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("contrats", "0002_regime_duree_validation_consultation"),
        ("prestations", "0008_typeexamen_hospitalisation_examenmedical"),
    ]

    operations = [
        migrations.AddField(
            model_name="medicament",
            name="code",
            field=models.CharField(
                help_text="Code du médicament", max_length=255, null=True
            ),
        ),
        migrations.AddField(
            model_name="medicament",
            name="dci",
            field=models.TextField(
                blank=True, help_text="molecule du médicament", null=True
            ),
        ),
        migrations.AddField(
            model_name="medicament",
            name="molecule",
            field=models.TextField(
                blank=True, help_text="categorie du médicament", null=True
            ),
        ),
        migrations.AddField(
            model_name="medicament",
            name="regime",
            field=models.ForeignKey(
                help_text="Régime d'assurance associé",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="medicamentregime",
                to="contrats.regime",
            ),
        ),
        migrations.AddField(
            model_name="medicament",
            name="typem",
            field=models.TextField(
                blank=True, help_text="type du médicament", null=True
            ),
        ),
        migrations.AlterField(
            model_name="medicament",
            name="nom",
            field=models.CharField(
                help_text="Nom du médicament", max_length=255, null=True
            ),
        ),
    ]
