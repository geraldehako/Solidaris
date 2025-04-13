from django.db import models


# ======================= RÉGIME =======================
class Regime(models.Model):
    """
    Modèle représentant un régime d'assurance.
    """
    nom = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nom du régime (ex: Régime Général, Régime Spécial)"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Description détaillée du régime"
    )
    taux_couverture = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Taux en % de couverture des frais médicaux (ex: 75.50)"
    )
    tiers_payant = models.BooleanField(
        default=True,
        help_text="Indique si le tiers payant est activé pour ce régime"
    )
    duree_validation_consultation = models.PositiveIntegerField(
        default=14,
        help_text="Durée de validité en jours pour une prise en charge en consultation"
    )
    duree_validation_pharmacie = models.PositiveIntegerField(
        default=7,
        help_text="Durée de validité en jours pour une prise en charge en pharmacie"
    )
    duree_validation_optique = models.PositiveIntegerField(
        default=730,
        help_text="Durée de validité en jours pour une prise en charge en optique"
    )
    plafond_annuel_couverture =models.IntegerField(null=True, blank=True,
        help_text="Plafond annuel de couverture en FCFA (laisser vide pour illimité)"
    )
    plafond_adhesion =models.IntegerField(null=True, blank=True,
        help_text="Plafond annuel de l'adhésion en FCFA (laisser vide pour illimité)"
    )
    plafond_cotisation_mensuelle =models.IntegerField(null=True, blank=True,
        help_text="Plafond annuel de l'adhésion en FCFA (laisser vide pour illimité)"
    ) 
    actif = models.BooleanField(
        default=True,
        help_text="Indique si le régime est actif et peut être utilisé"
    )

    def __str__(self):
        return f"{self.nom} ({'Tiers Payant' if self.tiers_payant else 'Non Tiers Payant'})" 

    def est_actif(self):
        """
        Vérifie si le régime est actif.
        """
        return self.actif

    def get_duree_validation_consultation(self):
        """
        Retourne la durée de validation en sante (par défaut ou spécifique).
        """
        return self.duree_validation_consultation
    
    def get_duree_validation_pharmacie(self):
        """
        Retourne la durée de validation en pharmacie (par défaut ou spécifique).
        """
        return self.duree_validation_pharmacie

    def get_taux_couverture(self):
        """
        Retourne le taux de couverture du régime.
        """
        return self.taux_couverture

    def get_plafond_annuel(self):
        """
        Retourne le plafond annuel de couverture ou None si illimité.
        """
        return self.plafond_annuel_couverture

    class Meta:
        verbose_name = "Régime"
        verbose_name_plural = "Régimes"
        ordering = ['nom']


# ======================= GARANTIE =======================
class Garantie(models.Model):
    """
    Modèle représentant une garantie spécifique associée à un régime.
    """
    regime = models.ForeignKey(
        Regime,
        on_delete=models.CASCADE,
        related_name="garanties",
        help_text="Régime associé à cette garantie"
    )
    nom = models.CharField(
        max_length=100,
        help_text="Nom de la garantie (ex: Hospitalisation, Optique)"
    )
    plafond_annuel = models.IntegerField(null=True, blank=True,
        help_text="Plafond annuel en FCFA (ex: 100000.00 FCFA)"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Description détaillée de la garantie"
    )

    def __str__(self):
        return f"{self.nom} - Plafond: {self.plafond_annuel:.2f} FCFA"

    class Meta:
        unique_together = ('regime', 'nom')  # Un nom de garantie doit être unique pour un régime donné.
        verbose_name = "Garantie"
        verbose_name_plural = "Garanties"
        ordering = ['regime', 'nom']
