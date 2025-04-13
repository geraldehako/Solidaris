from django.db import models
from django.contrib.auth.models import AbstractUser
from centres.models import CentreSante
from mutualistes.models import Mutualiste
from centres.models import Groupe

# ======================= UTILISATEUR =======================
class Utilisateur(AbstractUser):
    ROLE_CHOICES = [
        ('superadmin', 'Super Administrateur'),
        ('gestionnaire', 'Gestionnaire'),
        ('point_focal', 'Point Focal'),
        ('mutualiste', 'Mutualiste'),
        ('centre_sante', 'Centre de Santé'),
        ('pharmacie', 'pharmacie'),
        ('medecin_conseil', 'Médecin Conseil'),
    ]
    photo = models.ImageField(
        upload_to='utilisateurs/photos/', 
        null=True, 
        blank=True, 
        help_text="Photo de profil de l'utilisateur"
    )
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='gestionnaire',
        help_text="Rôle principal de l'utilisateur dans le système"
    )
    groupe = models.ForeignKey(
        Groupe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="utilisateurs",
        help_text="Groupe associé (pour les points focaux uniquement)"
    )
    mutualiste = models.OneToOneField(
        'mutualistes.Mutualiste',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="utilisateur",
        help_text="Lien avec le mutualiste si l'utilisateur est un mutualiste"
    )
    centre_sante = models.OneToOneField(
        'centres.CentreSante',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="utilisateur",
        help_text="Lien avec le centre de santé si l'utilisateur représente un centre"
    )
    telephone = models.CharField(
        max_length=15, 
        null=True, 
        blank=True, 
        help_text="Numéro de téléphone de l'utilisateur"
    )

    def est_superadmin(self):
        return self.role == 'superadmin'

    def est_gestionnaire(self):
        return self.role == 'gestionnaire'

    def est_point_focal(self):
        return self.role == 'point_focal'

    def est_mutualiste(self):
        return self.role == 'mutualiste' and self.mutualiste is not None

    def est_centre_sante(self):
        return self.role == 'centre_sante' and self.centre_sante is not None

    def obtenir_profil(self):
        """
        Retourne le modèle associé selon le rôle.
        """
        if self.est_mutualiste():
            return self.mutualiste
        elif self.est_centre_sante():
            return self.centre_sante
        return None

    def __str__(self):
        profil = self.obtenir_profil()
        profil_str = f" - {profil}" if profil else ""
        return f"{self.username} ({self.get_role_display()}){profil_str}"

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ['username']


# ======================= CONNEXIONS DES UTILISATEURS =======================
class ConnexionUtilisateur(models.Model):
    utilisateur = models.ForeignKey(
        Utilisateur, 
        on_delete=models.CASCADE, 
        related_name="connexions",
        help_text="Utilisateur connecté"
    )
    adresse_ip = models.GenericIPAddressField(
        help_text="Adresse IP de l'utilisateur lors de la connexion"
    )
    date_connexion = models.DateTimeField(
        auto_now_add=True, 
        help_text="Date et heure de la connexion"
    )

    def __str__(self):
        return f"Connexion: {self.utilisateur.username} - {self.date_connexion}"

    class Meta:
        verbose_name = "Connexion utilisateur"
        verbose_name_plural = "Connexions des utilisateurs"
        ordering = ['-date_connexion']

# ======================= HISTORIQUE DES ACTIONS =======================
class HistoriqueUtilisateur(models.Model):
    utilisateur = models.ForeignKey(
        Utilisateur, 
        on_delete=models.CASCADE, 
        related_name="historiques",
        help_text="Utilisateur ayant effectué l'action"
    )
    action = models.CharField(
        max_length=255, 
        help_text="Description de l'action effectuée"
    )
    date_action = models.DateTimeField(
        auto_now_add=True, 
        help_text="Date et heure de l'action"
    )
    details = models.JSONField(
        null=True, 
        blank=True, 
        help_text="Détails supplémentaires de l'action (format JSON)"
    )

    def __str__(self):
        return f"Historique: {self.utilisateur.username} - {self.action} ({self.date_action})"

    class Meta:
        verbose_name = "Historique utilisateur"
        verbose_name_plural = "Historiques des utilisateurs"
        ordering = ['-date_action']
