from datetime import date, timedelta
from django.db import models
from mutualistes.models import Mutualiste
from utilisateurs.models import Utilisateur



# ======================= HISTORIQUE CODE MATRICULE =======================
class HistoriqueCodeMatricule(models.Model):
    """
    Historique des codes matricules pour un mutualiste.
    """
    mutualiste = models.ForeignKey(
        Mutualiste,
        on_delete=models.CASCADE,
        related_name="historique_codes",
        help_text="Mutualiste associé à ce code matricule"
    )
    ancien_code = models.CharField(max_length=9, help_text="Ancien code matricule")
    date_changement = models.DateTimeField(auto_now_add=True, help_text="Date du changement de code matricule")

    def __str__(self):
        return f"{self.mutualiste.utilisateur.username} - Ancien code: {self.ancien_code}"


# ======================= CATÉGORIE D'AFFECTION =======================
class CategorieAffection(models.Model):
    """
    Catégorie des affections (par exemple : Chronique, Aiguë).
    """
    nom = models.CharField(
        max_length=50,
        unique=True,
        help_text="Nom de la catégorie (ex: Chronique, Aiguë, etc.)"
    )
    description = models.TextField(null=True, blank=True, help_text="Description de la catégorie")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Date de création",null=True)
    
    def __str__(self): 
        return self.nom

    class Meta:
        verbose_name = "Catégorie d'affection"
        verbose_name_plural = "Catégories d'affection"
        ordering = ['nom']


# ======================= CODE D'AFFECTION =======================
class CodeAffection(models.Model):
    """
    Code associé à une affection médicale spécifique.
    """
    code = models.CharField(
        max_length=10,
        unique=True,
        help_text="Code unique de l'affection (ex: A001, C123, etc.)"
    )
    nom = models.CharField(
        max_length=100,
        help_text="Nom de l'affection (ex: Hypertension, Diabète)"
    )
    description = models.TextField(null=True, blank=True, help_text="Description détaillée de l'affection")
    categorie = models.ForeignKey(
        CategorieAffection,
        on_delete=models.SET_NULL,
        null=True,
        related_name="affections",
        help_text="Catégorie associée à cette affection"
    )
    date_creation = models.DateField(auto_now_add=True, help_text="Date de création du code d'affection")
    updated_at = models.DateTimeField(auto_now=True, help_text="Dernière mise à jour du code d'affection")
    
    def __str__(self):
        return f"{self.code} - {self.nom}"

    class Meta:
        verbose_name = "Code d'affection"
        verbose_name_plural = "Codes d'affection"
        ordering = ['code']


# ======================= ORDONNANCE =======================
class Ordonnance(models.Model):
    """
    Modèle représentant une ordonnance médicale pour un mutualiste.
    """
    mutualiste = models.ForeignKey(
        Mutualiste,
        on_delete=models.CASCADE,
        related_name="ordonnances",
        help_text="Mutualiste pour lequel l'ordonnance est émise"
    )
    date_emission = models.DateField(auto_now_add=True, help_text="Date d'émission de l'ordonnance")
    renouvelable = models.BooleanField(default=False, help_text="Indique si l'ordonnance est renouvelable")
    periodicite = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Périodicité du renouvellement (en jours)"
    )
    valide_jusquau = models.DateField(
        null=True,
        blank=True,
        help_text="Date limite pour renouveler l'ordonnance"
    )
    updated_at = models.DateTimeField(auto_now=True, help_text="Dernière mise à jour de l'ordonnance")
    
    def renouveler(self):
        """
        Renouvelle l'ordonnance en prolongeant sa validité.
        """
        if self.renouvelable and self.periodicite:
            self.valide_jusquau = date.today() + timedelta(days=self.periodicite)
            self.save()

    def __str__(self):
        return f"Ordonnance - Mutualiste: {self.mutualiste.utilisateur.username}"

    def is_valid(self):
        """
        Vérifie si l'ordonnance est encore valide.
        """
        return self.valide_jusquau is None or self.valide_jusquau >= date.today()

    class Meta:
        verbose_name = "Ordonnance"
        verbose_name_plural = "Ordonnances"
        ordering = ['-date_emission']