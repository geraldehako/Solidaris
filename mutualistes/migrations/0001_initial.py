# Generated by Django 4.1.7 on 2024-12-20 22:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("contrats", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Mutualiste",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "numero_contrat",
                    models.CharField(
                        editable=False,
                        help_text="Numéro unique du contrat d'assurance généré automatiquement",
                        max_length=12,
                        unique=True,
                    ),
                ),
                (
                    "photo",
                    models.ImageField(
                        blank=True,
                        help_text="Photo du mutualiste",
                        null=True,
                        upload_to="mutualistes/photos/",
                    ),
                ),
                (
                    "code_matricule",
                    models.CharField(
                        editable=False,
                        help_text="Code matricule généré automatiquement",
                        max_length=9,
                        unique=True,
                    ),
                ),
                (
                    "date_naissance",
                    models.DateField(help_text="Date de naissance du mutualiste"),
                ),
                (
                    "date_adhesion",
                    models.DateField(
                        auto_now_add=True, help_text="Date d'adhésion à l'assurance"
                    ),
                ),
                (
                    "statut",
                    models.BooleanField(
                        default=True, help_text="Statut actif ou inactif"
                    ),
                ),
                (
                    "regime",
                    models.ForeignKey(
                        help_text="Régime d'assurance associé",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="mutualistes",
                        to="contrats.regime",
                    ),
                ),
            ],
            options={
                "verbose_name": "Mutualiste",
                "verbose_name_plural": "Mutualistes",
                "ordering": ["numero_contrat"],
            },
        ),
        migrations.CreateModel(
            name="Beneficiaire",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "nom",
                    models.CharField(help_text="Nom du bénéficiaire", max_length=100),
                ),
                (
                    "prenom",
                    models.CharField(
                        help_text="Prénom du bénéficiaire", max_length=100
                    ),
                ),
                (
                    "type_filiation",
                    models.CharField(
                        choices=[("conjoint", "Conjoint"), ("enfant", "Enfant")],
                        help_text="Lien de parenté avec le mutualiste",
                        max_length=50,
                    ),
                ),
                (
                    "date_naissance",
                    models.DateField(help_text="Date de naissance du bénéficiaire"),
                ),
                (
                    "sexe",
                    models.CharField(
                        choices=[("M", "Masculin"), ("F", "Féminin")],
                        help_text="Sexe du bénéficiaire",
                        max_length=10,
                    ),
                ),
                (
                    "mutualiste",
                    models.ForeignKey(
                        help_text="Mutualiste auquel appartient ce bénéficiaire",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="beneficiaires",
                        to="mutualistes.mutualiste",
                    ),
                ),
            ],
            options={
                "verbose_name": "Bénéficiaire",
                "verbose_name_plural": "Bénéficiaires",
                "ordering": ["nom", "prenom"],
            },
        ),
    ]
