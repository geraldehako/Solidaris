# Generated by Django 4.1.7 on 2024-12-20 22:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("mutualistes", "0001_initial"),
        ("centres", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Remboursement",
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
                    "montant",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="Montant remboursé en FCFA",
                        max_digits=10,
                    ),
                ),
                (
                    "date_remboursement",
                    models.DateField(
                        auto_now_add=True,
                        help_text="Date à laquelle le remboursement a été effectué",
                    ),
                ),
                (
                    "statut",
                    models.BooleanField(
                        default=False,
                        help_text="Statut du remboursement (True = Remboursé)",
                    ),
                ),
                (
                    "mutualiste",
                    models.ForeignKey(
                        help_text="Mutualiste bénéficiant du remboursement",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="remboursements",
                        to="mutualistes.mutualiste",
                    ),
                ),
            ],
            options={
                "verbose_name": "Remboursement",
                "verbose_name_plural": "Remboursements",
                "ordering": ["-date_remboursement"],
            },
        ),
        migrations.CreateModel(
            name="Facture",
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
                    "date_debut",
                    models.DateField(help_text="Début de la période de facturation"),
                ),
                (
                    "date_fin",
                    models.DateField(help_text="Fin de la période de facturation"),
                ),
                (
                    "date_emission",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Date à laquelle la facture a été émise",
                    ),
                ),
                (
                    "total_mutualiste",
                    models.DecimalField(
                        decimal_places=2,
                        default=0.0,
                        help_text="Montant total à la charge des mutualistes",
                        max_digits=10,
                    ),
                ),
                (
                    "total_mutuelle",
                    models.DecimalField(
                        decimal_places=2,
                        default=0.0,
                        help_text="Montant total pris en charge par la mutuelle",
                        max_digits=10,
                    ),
                ),
                (
                    "total_general",
                    models.DecimalField(
                        decimal_places=2,
                        default=0.0,
                        help_text="Montant total de la facture",
                        max_digits=10,
                    ),
                ),
                (
                    "date_paiement",
                    models.DateField(
                        blank=True,
                        help_text="Date de paiement de la facture",
                        null=True,
                    ),
                ),
                (
                    "statut",
                    models.CharField(
                        choices=[("payee", "Payée"), ("impayee", "Impayée")],
                        default="impayee",
                        help_text="Statut de la facture (payée ou impayée)",
                        max_length=20,
                    ),
                ),
                (
                    "centre",
                    models.ForeignKey(
                        help_text="Centre de santé ou pharmacie émettant la facture",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="factures",
                        to="centres.centresante",
                    ),
                ),
            ],
            options={
                "verbose_name": "Facture",
                "verbose_name_plural": "Factures",
                "ordering": ["-date_emission"],
            },
        ),
    ]
