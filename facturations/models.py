from django.db import models
from mutualistes.models import Mutualiste
from prestations.models import Prestation, PriseEnCharge
from centres.models import CentreSante

from django.db import models
from django.utils.timezone import now
import calendar
from django.core.validators import FileExtensionValidator

# ======================= FACTURE =======================
class Facture(models.Model):
    """
    Modèle représentant une facture émise par un centre de santé.
    """
    STATUTS_FACTURE = [
        ('payee', 'Payée'),
        ('impayee', 'Impayée'),
    ]

    centre = models.ForeignKey(
        CentreSante,
        on_delete=models.CASCADE,
        related_name="factures",
        help_text="Centre de santé ou pharmacie émettant la facture"
    )
    numero_facture = models.CharField(
        max_length=10,
        editable=False,
        null=True,
        help_text="Numéro unique de la facture au format MMYYYY pour chaque centre"
    )
    intitule_facture = models.CharField(
        max_length=50,
        editable=False,
        null=True,
        help_text="Intitulé de la facture sous la forme 'Mois Année'"
    )
    date_debut = models.DateField(
        editable=False,
        help_text="Début de la période de facturation (1er jour du mois)"
    )
    date_fin = models.DateField(
        editable=False,
        help_text="Fin de la période de facturation (dernier jour du mois)"
    )
    date_emission = models.DateTimeField(
        auto_now_add=True,
        help_text="Date à laquelle la facture a été émise"
    )
    prises_en_charge = models.ManyToManyField(
        PriseEnCharge,
        related_name="factures",
        help_text="Prises en charge incluses dans la facture"
    )
    total_mutualiste = models.IntegerField(
        default=0,
        help_text="Montant total à la charge des mutualistes"
    )
    total_mutuelle = models.IntegerField(
        default=0,
        help_text="Montant total pris en charge par la mutuelle"
    )
    total_general = models.IntegerField(
        default=0,
        help_text="Montant total de la facture"
    )
    date_paiement = models.DateField(
        null=True,
        blank=True,
        help_text="Date de paiement de la facture"
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUTS_FACTURE,
        default='impayee',
        help_text="Statut de la facture (payée ou impayée)"
    )

    class Meta:
        verbose_name = "Facture"
        verbose_name_plural = "Factures"
        ordering = ['-date_emission']
        constraints = [
            models.UniqueConstraint(
                fields=['centre', 'numero_facture'],
                name="unique_numero_facture_par_centre"
            ),
            models.UniqueConstraint(
                fields=['centre', 'intitule_facture'],
                name="unique_intitule_facture_par_centre"
            ),
        ]

    def save(self, *args, **kwargs):
        """
        Génère automatiquement le numéro, l'intitulé et les dates de la facture.
        """
        if not self.id:  # Générer uniquement lors de la création
            current_date = now().date()
            mois = current_date.month
            annee = current_date.year
            dernier_jour = calendar.monthrange(annee, mois)[1]

            self.numero_facture = f"{mois:02}{annee}"
            self.intitule_facture = f"{current_date.strftime('%B')} {annee}".capitalize()
            self.date_debut = f"{annee}-{mois:02}-01"
            self.date_fin = f"{annee}-{mois:02}-{dernier_jour}"

        super().save(*args, **kwargs)

    def calculer_totaux(self):
        """
        Calcule les montants totaux des mutualistes et de la mutuelle, 
        ainsi que le montant général de la facture.
        """
        total_mutualiste = 0
        total_mutuelle = 0

        for pec in self.prises_en_charge.all():
            for prestation in pec.prestations.all():
                total_mutualiste += prestation.part_mutualiste
                total_mutuelle += prestation.part_mutuelle

        self.total_mutualiste = total_mutualiste
        self.total_mutuelle = total_mutuelle
        self.total_general = total_mutualiste + total_mutuelle
        self.save()

    def __str__(self):
        return f"Facture {self.numero_facture} - {self.intitule_facture} - {self.centre.nom}"


# ======================= REMBOURSEMENT =======================
class Remboursement(models.Model):
    """
    Modèle représentant un remboursement effectué par la mutuelle.
    """
    mutualiste = models.ForeignKey(
        Mutualiste,
        on_delete=models.CASCADE,
        related_name="remboursements",
        help_text="Mutualiste bénéficiant du remboursement"
    )
    montant = models.IntegerField(null=True, blank=True,
        help_text="Montant remboursé en FCFA"
    )
    date_remboursement = models.DateField(
        auto_now_add=True,
        help_text="Date à laquelle le remboursement a été effectué"
    )
    statut = models.BooleanField(
        default=False,
        help_text="Statut du remboursement (True = Remboursé)"
    )
    justif = models.FileField(
        upload_to="justif/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'png'])]
    )
    class Meta:
        verbose_name = "Remboursement"
        verbose_name_plural = "Remboursements"
        ordering = ['-date_remboursement'] 

    def __str__(self):
        return f"Remboursement {self.id} - {self.mutualiste.utilisateur.username} - {self.montant:.2f} FCFA"

