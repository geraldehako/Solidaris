from django.db import models
from django.utils.timezone import now
import calendar
from centres.models import Groupe
from utilisateurs.models import Utilisateur
from django.core.validators import FileExtensionValidator

# ======================= COTISATION =======================
class Cotisation(models.Model):
    """
    Modèle représentant une cotisation émise par un centre de santé.
    """
    STATUTS_COTISATION = [
        ('payee', 'Payée'),
        ('impayee', 'Impayée'),
    ]

    groupe = models.ForeignKey(
        Groupe,
        on_delete=models.CASCADE,
        related_name="cotisations",
        help_text="Groupe émettant la cotisation"
    )
    numero_cotisation = models.CharField(
        max_length=10,
        editable=False,
        unique=True,
        null=True,
        help_text="Numéro unique de la cotisation au format MMYYYY pour chaque groupe"
    )
    intitule_cotisation = models.CharField(
        max_length=50,
        editable=False,
        null=True,
        help_text="Intitulé de la cotisation sous la forme 'Mois Année'"
    )
    date_debut = models.DateField(
        editable=False,
        help_text="Début de la période de cotisation (1er jour du mois)"
    )
    date_fin = models.DateField(
        editable=False,
        help_text="Fin de la période de cotisation (dernier jour du mois)"
    )
    date_emission = models.DateTimeField(
        auto_now_add=True,
        help_text="Date à laquelle la cotisation a été émise"
    )
    total_adhesion = models.IntegerField(
        default=0,
        help_text="Montant total de l'adhésion"
    )
    total_cotisation = models.IntegerField(
        default=0,
        help_text="Montant total à la charge des mutualistes"
    )
    total_general = models.IntegerField(
        default=0,
        help_text="Montant total de la facture"
    )
    total_payer = models.IntegerField(
        default=0,
        help_text="Montant total pris en charge par la mutuelle"
    )
    total_restant = models.IntegerField(
        default=0,
        help_text="Montant restant à payer"
    )
    date_paiement = models.DateField(
        null=True,
        blank=True,
        help_text="Date de paiement de la facture"
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUTS_COTISATION,
        default='impayee',
        help_text="Statut de la facture (payée ou impayée)"
    )

    class Meta:
        verbose_name = "Cotisation"
        verbose_name_plural = "Cotisations"
        ordering = ['-date_emission']
        constraints = [
            models.UniqueConstraint(
                fields=['groupe', 'numero_cotisation'],
                name="unique_numero_cotisation_par_groupe"
            ),
            models.UniqueConstraint(
                fields=['groupe', 'intitule_cotisation'],
                name="unique_intitule_cotisation_par_groupe"
            ),
        ]

    def save(self, *args, **kwargs):
        """
        Génère automatiquement le numéro, l'intitulé et les dates de la cotisation.
        """
        if not self.id:  # Générer uniquement lors de la création
            current_date = now().date()
            mois = current_date.month
            annee = current_date.year
            dernier_jour = calendar.monthrange(annee, mois)[1]

            self.numero_cotisation = f"{mois:02}{annee}"
            self.intitule_cotisation = f"{current_date.strftime('%B')} {annee}".capitalize()
            self.date_debut = now().replace(day=1).date()
            self.date_fin = now().replace(day=dernier_jour).date()

        super().save(*args, **kwargs)

    def calculer_totaux(self):
        """
        Calcule les montants totaux des mutualistes et de la mutuelle, 
        ainsi que le montant général de la facture.
        """
        self.total_general = self.total_cotisation + self.total_adhesion
        self.total_restant = self.total_general - self.total_payer

        if self.total_restant == 0:
            self.statut = "payee"
        else:
            self.statut = "impayee"

        self.save()

    def __str__(self):
        return f"Facture {self.numero_cotisation} - {self.intitule_cotisation} - {self.groupe.nom}"

# ======================= MOUVEMENTS PAIEMENTS ============================ 
class MouvementPaiement(models.Model):
    cotisation = models.ForeignKey(Cotisation, on_delete=models.CASCADE, related_name='paiements')
    montant = models.IntegerField(default=0)
    date_paiement = models.DateField(auto_now_add=True)
    mode_paiement = models.CharField(max_length=50, choices=[('Espèces', 'Espèces'), ('Virement', 'Virement')])
    reference = models.CharField(max_length=100, blank=True, null=True)
    fichier_virement = models.FileField(
        upload_to="ordre_paiement/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'png'])]
    )
    created_by = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True) 

    def __str__(self):
        return f"{self.montant} FCFA - {self.date_paiement}"