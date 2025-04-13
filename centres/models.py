from django.db import models
from jsonschema import ValidationError

# ======================= GROUPE =======================
class Groupe(models.Model):
    """
    Représente un groupe (ou diocèse) auquel les centres de santé peuvent être associés.
    """
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.nom


# ======================= CENTRE DE SANTÉ ============================ 
class CentreSante(models.Model):
    """
    Représente un centre de santé tel qu'un hôpital, clinique, pharmacie, etc.
    """
    TYPES_CENTRE = [
        ('hopital', 'Hôpital'),
        ('clinique', 'Clinique'),
        ('pharmacie', 'Pharmacie'),
        ('laboratoire', 'Laboratoire'),
        ('lunetterie', 'Lunetterie'),
    ] 
    nom = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=20, choices=TYPES_CENTRE)
    adresse = models.CharField(max_length=255)
    telephone = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    groupe = models.ForeignKey(
        'Groupe',  # Référence au modèle Groupe
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="centres_sante"
    )
    statut = models.BooleanField(
        default=True, 
        help_text="Statut actif ou inactif"
    )
    observations = models.CharField(max_length=255,default="R.A.S")

    def __str__(self):
        return f"{self.nom} ({self.get_type_display()})"
    
# ======================= ASSOCIATION CENTRE ET MEDECIN =======================
class MedecinTraitant(models.Model):
    nom = models.CharField(max_length=100, help_text="Nom du médecin")
    prenom = models.CharField(max_length=100, help_text="Prénom du médecin")
    specialite = models.CharField(max_length=150, help_text="Spécialité médicale")
    email = models.EmailField(unique=True, help_text="Email professionnel du médecin")
    telephone = models.CharField(max_length=20, help_text="Numéro de téléphone du médecin")
    numero_ordre = models.CharField(max_length=25, help_text="ordre du médecin")
    centre_sante = models.ForeignKey(
        CentreSante, 
        on_delete=models.CASCADE, 
        related_name="medecins", 
        help_text="Centre de santé où travaille le médecin"
    )
    date_ajout = models.DateTimeField(auto_now_add=True, help_text="Date d'enregistrement du médecin")

    def __str__(self):
        return f"Dr. {self.nom} {self.prenom} - {self.specialite} - {self.numero_ordre}"
    
# ======================= ASSOCIATION CENTRE ET PRESTATION =======================
class CentreSantePrestation(models.Model):
    """
    Associe une prestation spécifique à un centre de santé avec un tarif personnalisé et une disponibilité.
    """
    centre_sante = models.ForeignKey(
        'CentreSante',  # Référence au modèle CentreSante
        on_delete=models.CASCADE,
        related_name='prestations'
    )
    prestation = models.ForeignKey(
        'prestations.ListeDesPrestations',  # Référence au modèle ListeDesPrestations dans l'application 'prestations'
        on_delete=models.CASCADE,
        related_name='centres_associes'
    )
    tarif_personnalise = models.IntegerField(
        null=True,
        blank=True,
        help_text="Tarif spécifique pour cette prestation dans ce centre (entier sans virgule)."
    )
    disponible = models.BooleanField(default=True, help_text="Indique si la prestation est disponible dans ce centre.")

    class Meta:
        unique_together = ('centre_sante', 'prestation')  # Une association unique entre centre et prestation
        verbose_name = "Prestation Centre Santé"
        verbose_name_plural = "Prestations Centres Santé"

    def __str__(self):
        status = "Disponible" if self.disponible else "Non Disponible"
        return f"{self.prestation.nom} - {self.centre_sante.nom} ({status})"

    def clean(self):
        """
        Validation : Le tarif personnalisé doit être supérieur à zéro s'il est défini.
        """
        if self.tarif_personnalise is not None and self.tarif_personnalise <= 0:
            raise ValidationError("Le tarif personnalisé doit être supérieur à zéro.")
