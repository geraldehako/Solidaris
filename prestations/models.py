import uuid
from django.db import models

# Create your models here.
from django.db import models
from django.core.exceptions import ValidationError
from centres.models import CentreSante, MedecinTraitant
from mutualistes.models import Mutualiste,Beneficiaire
from utilisateurs.models import Utilisateur
from contrats.models import Regime
from datetime import datetime, timedelta, date, timezone
from decimal import Decimal
from django.core.validators import FileExtensionValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.mail import send_mail

# ======================= PRISE EN CHARGE =======================
class NaturePriseEnCharge(models.Model):
    nature = models.CharField(max_length=100, unique=True, help_text="Nature de la prise en charge")

    def __str__(self):
        return self.nature
    
    class Meta:
        ordering = ['nature']


class PriseEnCharge(models.Model):
    nature = models.ForeignKey(
        NaturePriseEnCharge, 
        on_delete=models.CASCADE, 
        null=True,
        related_name="natureprises_en_charge",
        help_text="Le mutualiste ayant cette nature de prise en charge"
    )
    
    mutualiste = models.ForeignKey(
        Mutualiste, 
        on_delete=models.CASCADE, 
        related_name="prises_en_charge",
        help_text="Le mutualiste ayant cette prise en charge"
    )
    beneficiaire = models.ForeignKey(
        Beneficiaire,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="prises_en_charge",
        help_text="Bénéficiaire concerné par cette prise en charge, s'il ne s'agit pas du mutualiste"
    )
    centre = models.ForeignKey(
        CentreSante, 
        on_delete=models.CASCADE, 
        related_name="prises_en_charge",
        help_text="Le centre de santé ayant pris en charge le mutualiste"
    )
    medecin_traitant = models.ForeignKey(
        MedecinTraitant, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    date_prise_en_charge = models.DateField(
        help_text="Date à laquelle la prise en charge a eu lieu"
    )  
    date_creation = models.DateTimeField(
        auto_now_add=True, 
        help_text="Date et heure de la création du dossier"
    )
    numero_dossier = models.CharField(
        max_length=10, 
        unique=True,
        help_text="Numéro unique du dossier de prise en charge, format AAMMDDHHMM"
    )
    duree_validite = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        help_text="Durée de validité en jours pour cette prise en charge"
    )

    def save(self, *args, **kwargs):
        if not self.numero_dossier:
            now = datetime.now()
            self.numero_dossier = now.strftime('%y%m%d%H%M')  # Format AAMMDDHHMM
        super().save(*args, **kwargs)
        
    def est_valide(self):
        """
        Vérifie si la prise en charge est encore valide.
        """
        duree = self.duree_validite or self.get_duree_par_defaut()
        date_expiration = self.date_prise_en_charge + timedelta(days=duree)
        return date.today() <= date_expiration

    def get_duree_par_defaut(self):
        """
        Récupère la durée par défaut en fonction du régime.
        """
        regime = self.mutualiste.regime
        return regime.duree_validation_pharmacie if regime else 7

    def clean(self):
        """
        Validation des champs nécessaires.
        """
        if not self.mutualiste and not self.beneficiaire:
            raise ValidationError("Une prise en charge doit concerner soit un mutualiste, soit un bénéficiaire.")
        if self.date_prise_en_charge > date.today():
            raise ValidationError("La date de prise en charge ne peut pas être dans le futur.")

    def __str__(self):
        if self.beneficiaire:
            return f"Prise en charge {self.numero_dossier} - {self.beneficiaire.nom} {self.beneficiaire.prenom}"
        return f"Prise en charge {self.numero_dossier} - {self.mutualiste.nom} {self.mutualiste.prenom}"

    class Meta:
        verbose_name = "Prise en charge"
        verbose_name_plural = "Prises en charge"
        ordering = ['-date_creation']



# ======================= LISTE DES PRESTATIONS =======================
class ListeDesPrestations(models.Model):
    CATEGORIES_PRESTATION = [
        ('consultation', 'Consultation Médicale'),
        ('examen', 'Examen Médical'),
        ('analyse', 'Analyse de Laboratoire'),
        ('soin', 'Soin Infirmier'),
        ('medicament', 'Médicament'),
    ]
    nom = models.CharField(max_length=100, help_text="Nom de la prestation médicale")
    description = models.TextField(null=True, blank=True, help_text="Description détaillée de la prestation")
    categorie = models.CharField(max_length=20, choices=CATEGORIES_PRESTATION, help_text="Catégorie de la prestation")
    tarif_standard = models.IntegerField(null=True, blank=True, help_text="Tarif standard")
    actif = models.BooleanField(default=True, help_text="Indique si la prestation est active")
    soumis_a_validation = models.BooleanField(default=False, help_text="Validation préalable nécessaire ?")

    def __str__(self):
        return f"{self.nom} ({'Validation requise' if self.soumis_a_validation else 'Pas de validation'})"

    class Meta:
        verbose_name = "Liste des prestations"
        verbose_name_plural = "Listes des prestations"
        ordering = ['nom']


# ======================= PRESTATION RÉALISÉE =======================
class Prestation(models.Model):
    prise_en_charge = models.ForeignKey(PriseEnCharge, on_delete=models.CASCADE, related_name="prestations")
    centre_sante = models.ForeignKey(CentreSante, on_delete=models.CASCADE)
    prestation = models.ForeignKey(ListeDesPrestations, on_delete=models.CASCADE, related_name="prestation_realisee")
    medecin_traitant = models.ForeignKey(MedecinTraitant, on_delete=models.SET_NULL, null=True, blank=True)
    date_prestation = models.DateTimeField(auto_now_add=True)
    montant_total = models.IntegerField(null=True, blank=True)
    montant_pris_en_charge = models.IntegerField(null=True, blank=True)
    montant_moderateur = models.IntegerField(null=True, blank=True)
    tiers_payant = models.BooleanField(default=True)
    description = models.TextField(null=True, blank=True)
    statut_validation = models.BooleanField(default=False)
    date_validation = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.prestation.soumis_a_validation:
            self.statut_validation = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Prestation: {self.description} - {self.prise_en_charge.numero_dossier}"

    class Meta:
        verbose_name = "Prestation réalisée"
        verbose_name_plural = "Prestations réalisées"
        ordering = ['-date_prestation']


# ======================= HOSPITALISATION =======================
class Hospitalisation(models.Model):
    class StatutPriseEnCharge(models.TextChoices):
        EN_ATTENTE = "en_attente", _("En attente") 
        VALIDÉE = "validee", _("Validée") 
        REFUSÉE = "refusee", _("Refusée") 

    prise_en_charge = models.ForeignKey(PriseEnCharge, on_delete=models.CASCADE, related_name="prestationshospi")
    mutualiste = models.ForeignKey(Mutualiste, on_delete=models.CASCADE, related_name="hospitalisations")
    beneficiaire = models.ForeignKey(
        Beneficiaire,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="hospi",
        help_text="Bénéficiaire concerné par cette prise en charge, s'il ne s'agit pas du mutualiste"
    )
    centre_sante = models.ForeignKey(CentreSante, on_delete=models.CASCADE)
    date_admission = models.DateField(auto_now_add=True)
    date_sortie = models.DateField(null=True, blank=True)
    motif_hospitalisation = models.TextField(blank=True, null=True)
    fichier_hospitalisation = models.FileField(upload_to="resultats_hospitalisation/", blank=True, null=True)
    statut_prise_en_charge = models.CharField(
        max_length=20, choices=StatutPriseEnCharge.choices, default=StatutPriseEnCharge.EN_ATTENTE
    )
    motif_refus = models.TextField(blank=True, null=True)
    montant_prise_en_charge = models.IntegerField(null=True, blank=True)
    duree_validite = models.PositiveIntegerField(default=0)  # En jours
    
    # 🔴 Ajout de la relation avec Prestation
    prestations = models.ManyToManyField(Prestation, related_name="hospitalisations", blank=True)

    def est_valide(self):
        """ Vérifie si la prise en charge est toujours valide """
        if self.duree_validite > 0 and self.date_admission:
            date_expiration = self.date_admission + timezone.timedelta(days=self.duree_validite)
            return timezone.now().date() <= date_expiration
        return False

    def __str__(self):
        return f"Hospitalisation de {self.mutualiste} - {self.date_admission}"
    
# ======================= EXAMEN MEDICAL =======================
class TypeExamen(models.Model):
    libelle = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.libelle

# ✅ Modèle Examen Médical corrigé
class ExamenMedical(models.Model):
    class StatutExamen(models.TextChoices):
        EN_ATTENTE = "en_attente", _("En attente") 
        VALIDÉE = "validee", _("Validée") 
        REFUSÉE = "refusee", _("Refusée")

    prise_en_charge = models.ForeignKey(PriseEnCharge, on_delete=models.CASCADE, related_name="examens")
    mutualiste = models.ForeignKey(Mutualiste, on_delete=models.CASCADE, related_name="examens")
    beneficiaire = models.ForeignKey(
        Beneficiaire,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="ex",
        help_text="Bénéficiaire concerné par cette prise en charge, s'il ne s'agit pas du mutualiste"
    )
    type_examen = models.ForeignKey(ListeDesPrestations, on_delete=models.SET_NULL, null=True)
    centre_sante = models.ForeignKey(CentreSante, on_delete=models.SET_NULL, null=True, blank=True)
    date_prescription = models.DateField(default=timezone.now)
    date_realisation = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=StatutExamen.choices, default=StatutExamen.EN_ATTENTE)
    motif_refus = models.TextField(blank=True, null=True)
    resultat_texte = models.TextField(blank=True, null=True)
    fichier_resultat = models.FileField(
        upload_to="resultats_examens/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'png'])]
    )
    
    # 🔴 Ajout de la relation avec Prestation
    #prestations = models.ManyToManyField(Prestation, related_name="examens", blank=True)

    def clean(self):
        if self.date_realisation and self.date_realisation < self.date_prescription:
            raise ValidationError("La date de réalisation ne peut pas être antérieure à la date de prescription.")

    def clean_type_examen(self):
        if not self.type_examen:
            raise ValidationError("Le type d'examen est obligatoire.")
        return self.type_examen

    def __str__(self):
        return f"{self.type_examen} - {self.mutualiste} ({self.date_prescription})"

#examens = ExamenMedical.objects.select_related('mutualiste', 'prise_en_charge', 'centre_sante').all()


from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import ExamenMedical

#@receiver(post_save, sender=ExamenMedical)
#def notifier_medecin(sender, instance, **kwargs):
#    if instance.statut == ExamenMedical.StatutExamen.VALIDÉE:
#        message = f"L'examen {instance} pour {instance.mutualiste} a été réalisé."
#        # Envoi d'un e-mail au médecin
#        send_mail(
#            "Examen validé",
#            message,
#            "mandedec@gmail.com",
#            ["geraldomystere@yahoo.fr"],  # Remplace par le mail du médecin si besoin
#            fail_silently=False,
#        )




# ======================= MEDICAMENT =======================
class Medicament(models.Model):
    code = models.CharField(null=True,max_length=255, help_text="Code du médicament")
    nom = models.CharField(null=True,max_length=255, help_text="Nom du médicament")
    description = models.TextField(null=True, blank=True, help_text="Description du médicament")
    dci = models.TextField(null=True, blank=True, help_text="molecule du médicament")
    molecule = models.TextField(null=True, blank=True, help_text="categorie du médicament")
    typem = models.TextField(null=True, blank=True, help_text="type du médicament")
    regime = models.ForeignKey(
        Regime, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name="medicamentregime",
        help_text="Régime d'assurance associé"
    )
    disponible_en_pharmacie = models.BooleanField(default=True, help_text="Disponible en pharmacie")
    cout_unitaire = models.IntegerField(null=True, blank=True, help_text="Coût unitaire du médicament")

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Médicament"
        verbose_name_plural = "Médicaments"
        ordering = ['nom']

from django.db import models
from django.utils import timezone
import uuid

# ======================= PRESCRIPTION =======================
class Prescription(models.Model):
    class StatutPrescription(models.TextChoices):
        EN_ATTENTE = "en_attente", _("En attente") 
        RÉALISÉ = "realise", _("Réalisé") 
        ANNULÉ = "annule", _("Annulé") 
        FACTURÉ = "facture", _("facturé") 

    prise_en_charge = models.ForeignKey(
        'PriseEnCharge', 
        on_delete=models.CASCADE, 
        related_name="prescriptions"
    )
    date_prescription = models.DateField(default=timezone.now)
    code_prescription = models.CharField(
        max_length=9, 
        unique=True, 
        null=True, 
        editable=False, 
        help_text="Code matricule généré automatiquement"
    )
    statut = models.CharField(
        max_length=20, choices=StatutPrescription.choices, default=StatutPrescription.EN_ATTENTE
    )

    def save(self, *args, **kwargs):
        if not self.code_prescription:
            self.code_prescription = f"{self.date_prescription.year}{uuid.uuid4().hex[:3].upper()}ML"  # 4 + 3 + 2 = 9
        super().save(*args, **kwargs)

        
    def __str__(self):
        return f"Prescription {self.code_prescription} - {self.prise_en_charge.mutualiste.utilisateur.username}"

    class Meta:
        verbose_name = "Prescription"
        verbose_name_plural = "Prescriptions"
        ordering = ['-id']


# ======================= MÉDICAMENT PRESCRIS =======================
class MedicamentPrescris(models.Model):
    prestation_prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name="medicaments_prescris",
    )
    medicament = models.ForeignKey( 
        'Medicament',
        on_delete=models.CASCADE,
        related_name="prescriptions"
    )
    quantite_prescrite = models.PositiveIntegerField()
    posologie = models.CharField(max_length=255, null=True, blank=True)
    substitution_possible = models.BooleanField(default=False)
    medicament_substitue = models.ForeignKey(  # Nouveau champ
        'Medicament',
        on_delete=models.SET_NULL,
        related_name="substitutions",
        null=True,
        blank=True
    )

    def __str__(self):
        substitue = f" (Substitué par {self.medicament_substitue.nom})" if self.medicament_substitue else ""
        return f"{self.quantite_prescrite} x {self.medicament.nom}{substitue}"

    class Meta:
        unique_together = ("prestation_prescription", "medicament")
        verbose_name = "Médicament Prescrit"
        verbose_name_plural = "Médicaments Prescrits"

        
# ======================= PRESTATION PHARMACIE =======================
class PrestationPharmacie(models.Model):
    prescription = models.ForeignKey(
        'Prescription', 
        on_delete=models.CASCADE, 
        related_name="prestations_pharmacie",
        help_text="Prescription associée"
    )
    mutualiste = models.ForeignKey(
        'mutualistes.Mutualiste', 
        on_delete=models.CASCADE, 
        related_name="prestations_pharmacie",
        help_text="Mutualiste bénéficiant de la prestation"
    )
    beneficiaire = models.ForeignKey(
        Beneficiaire,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="pharm",
        help_text="Bénéficiaire concerné par cette prise en charge, s'il ne s'agit pas du mutualiste"
    )
    centre_sante = models.ForeignKey(
        'centres.CentreSante', 
        on_delete=models.CASCADE, 
        related_name="prestations_pharmacie",
        help_text="Centre de santé où la prestation a été effectuée"
    )
    date_prestation = models.DateTimeField(auto_now_add=True, help_text="Date et heure de la prestation")
    medicaments_utilises = models.ManyToManyField(
        Medicament, through="MedicamentUtilise", related_name="prestations_pharmacie"
    )
    montant_total = models.IntegerField(null=True, blank=True)
    part_mutualiste = models.IntegerField(null=True, blank=True)
    part_mutuelle = models.IntegerField(null=True, blank=True)

    def calculer_montant_total(self):
        total_medicaments = sum(
            util.quantite_servie * util.cout_unitaire
            for util in self.utilisations.all()  # Utilisation de `related_name` corrigé
        )
        taux_couverture = self.mutualiste.regime.taux_couverture / 100 if self.mutualiste.regime else Decimal('0.00')
        self.part_mutuelle = total_medicaments * taux_couverture
        self.part_mutualiste = total_medicaments - self.part_mutuelle
        self.montant_total = total_medicaments
        self.save()

    def __str__(self):
        return f"Prestation Pharmacie - {self.mutualiste.utilisateur.username}"

    class Meta:
        verbose_name = "Prestation Pharmacie"
        verbose_name_plural = "Prestations Pharmacie"
        ordering = ['-date_prestation']


# ======================= MEDICAMENT UTILISE =======================
class MedicamentUtilise(models.Model):
    prestation_pharmacie = models.ForeignKey(
        PrestationPharmacie,
        on_delete=models.CASCADE,
        related_name="utilisations",
        # default=1,  # Remplacez `1` par un ID valide existant
    )
    medicament = models.ForeignKey(  # Correction ici : `medicaments` devient `medicament`
        Medicament,
        on_delete=models.CASCADE,
        related_name="utilisations_medicaments"
    )
    quantite_servie = models.PositiveIntegerField()
    cout_unitaire = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.quantite_servie} x {self.medicament.nom}"

    class Meta:
        unique_together = ("prestation_pharmacie", "medicament")
        verbose_name = "Médicament Utilisé"
        verbose_name_plural = "Médicaments Utilisés"

 



# ======================= PRESTATION LUNETTERIE =======================
class PrestationLunetterie(models.Model):
    class StatutOptique(models.TextChoices):
        EN_ATTENTE = "en_attente", _("En attente") 
        VALIDÉE = "validee", _("Validée") 
        REFUSÉE = "refusee", _("Refusée")
        
    prise_en_charge = models.ForeignKey(
        PriseEnCharge, 
        on_delete=models.CASCADE,
        null=True,
        blank=True, 
        related_name="prestations_lunetterie", 
        help_text="Prise en charge associée à cette prestation"
    )
    mutualiste = models.ForeignKey(
        Mutualiste, 
        on_delete=models.CASCADE, 
        related_name="prestations_lunetterie", 
        help_text="Mutualiste bénéficiant de la prestation"
    )
    beneficiaire = models.ForeignKey(
        Beneficiaire,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="optik",
        help_text="Bénéficiaire concerné par cette prise en charge, s'il ne s'agit pas du mutualiste"
    )
    centre_sante = models.ForeignKey(
        CentreSante, 
        on_delete=models.CASCADE, 
        related_name="prestations_lunetterie", 
        help_text="Centre de santé où la prestation est effectuée"
    )
    date_prestation = models.DateTimeField(
        auto_now_add=True, 
        help_text="Date et heure de la prestation"
    )
    prestation = models.ForeignKey(ListeDesPrestations, on_delete=models.SET_NULL, null=True)
    medecin_traitant = models.ForeignKey(MedecinTraitant, on_delete=models.SET_NULL, null=True, blank=True)
    forfait_verres_et_montures = models.IntegerField(null=True, blank=True, 
        help_text="Forfait pour les verres et montures"
    )
    montant_total = models.IntegerField(null=True, blank=True, 
        help_text="Montant total de la prestation (forfait)"
    )
    description = models.TextField(
        null=True, 
        blank=True, 
        help_text="Description de la prestation"
    )
    statut = models.CharField(max_length=20, choices=StatutOptique.choices, default=StatutOptique.EN_ATTENTE)
    motif_refus = models.TextField(blank=True, null=True)
    fichier_resultat = models.FileField(
        upload_to="resultats_optique/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'png'])]
    )

    def __str__(self):
        return f"Prestation Lunetterie - Mutualiste: {self.mutualiste.utilisateur.username} - {self.date_prestation}"

    def calculer_montant_total(self):
        """
        Calcule le montant total de la prestation lunetterie en fonction du forfait.
        """
        self.montant_total = self.forfait_verres_et_montures
        self.save()
