from django.db import models
from centres.models import Groupe
from contrats.models import Regime
from django.core.exceptions import ValidationError
from datetime import date
import uuid
from django.db.models import Sum, Count
from django.utils.timezone import now

# ======================= MUTUALISTE =======================
class Mutualiste(models.Model):
    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]
    numero_contrat = models.CharField(
        max_length=12, 
        unique=True, 
        editable=False,
        help_text="Numéro unique du contrat d'assurance généré automatiquement"
    )
    photo = models.ImageField(
        upload_to='mutualistes/photos/', 
        null=True, 
        blank=True, 
        help_text="Photo du mutualiste", default='default/photo.png'
    )
    code_matricule = models.CharField(
        max_length=9, 
        unique=True, 
        editable=False, 
        help_text="Code matricule généré automatiquement"
    )
    nom = models.CharField(
        max_length=100, 
        help_text="Nom du mutualiste",
        null= True
    )
    prenom = models.CharField(
        max_length=100, 
        help_text="Prénom du mutualiste",
        null= True
    )
    date_naissance = models.DateField(
        help_text="Date de naissance du mutualiste"
    )
    sexe = models.CharField(
        max_length=10, 
        choices=SEXE_CHOICES, 
        help_text="Sexe du mutualiste",
        null= True
    )
    regime = models.ForeignKey(
        Regime, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name="mutualistes",
        help_text="Régime d'assurance associé"
    )
    groupe = models.ForeignKey(
        Groupe,  # Référence au modèle Groupe 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="diocèse"
    )
    date_adhesion = models.DateField(
        auto_now_add=True, 
        help_text="Date d'adhésion à l'assurance"
    )
    statut = models.BooleanField(
        default=True, 
        help_text="Statut actif ou inactif"
    )
    observations = models.CharField(max_length=255,default="R.A.S")
    telephone = models.CharField(
        max_length=15, 
        null=True, 
        blank=True, 
        help_text="Numéro de téléphone de l'utilisateur"
    )


    def save(self, *args, **kwargs):
        # Génération automatique des identifiants
        if not self.numero_contrat:
            self.numero_contrat = str(uuid.uuid4().int)[:12]

        if not self.code_matricule:
            if self.date_adhesion:
                self.code_matricule = f"{self.date_adhesion.year}{uuid.uuid4().hex[:5].upper()}ML"
            else:
                self.code_matricule = f"0000{uuid.uuid4().hex[:5].upper()}ML"
            
            # On s'assure que `code_matricule` respecte max_length=9
            self.code_matricule = self.code_matricule[:9]

        super().save(*args, **kwargs)



    @property
    def age(self):
        """
        Calcule l'âge actuel du mutualiste.
        """
        today = date.today()
        age = today.year - self.date_naissance.year
        if (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day):
            age -= 1
        return age

    @property
    def nombre_prises_en_charge(self):
        """
        Retourne le nombre total de prises en charge pour ce mutualiste.
        """
        return self.prises_en_charge.count()

    @property
    def montant_total_prestations(self):
        """
        Calcule le montant total cumulé des prestations pour ce mutualiste.
        """
        return self.prises_en_charge.aggregate(
            montant_total=Sum('prestations__montant_total')
        )['montant_total'] or 0.0
      

    def changer_code_matricule(self):
        """
        Change le code matricule en cas de perte ou vol de la carte.
        """
        self.code_matricule = self.generer_code_matricule()
        self.save()

    @property
    def dernier_dossier(self):
        """
        Retourne le dernier dossier de prise en charge pour ce mutualiste.
        """
        return self.prises_en_charge.order_by('-date_creation').first()


    def statistiques_prestations(self):
        """
        Retourne un résumé des statistiques importantes liées aux prestations
        ayant le statut de validation égal à 1.
        """
        stats = self.prises_en_charge.filter(prestations__statut_validation=1).aggregate(
            total_prestations=Count('prestations'),
            montant_total=Sum('prestations__montant_total'),
            part_mutuelle=Sum('prestations__montant_pris_en_charge'),
            part_mutualiste=Sum('prestations__montant_moderateur')
        )
        return {
            "total_prestations": stats['total_prestations'] or 0,
            "montant_total": stats['montant_total'] or 0.0,
            "part_mutuelle": stats['part_mutuelle'] or 0.0,
            "part_mutualiste": stats['part_mutualiste'] or 0.0,
    }


    def clean(self):
        """
        Validation de la date de naissance.
        """
        if self.date_naissance > date.today():
            raise ValidationError("La date de naissance ne peut pas être dans le futur.")

    def __str__(self):
        return f"{self.numero_contrat}-{self.code_matricule} - {self.nom} {self.prenom}"

    class Meta:
        verbose_name = "Mutualiste"
        verbose_name_plural = "Mutualistes"
        ordering = ['numero_contrat']
        indexes = [
        models.Index(fields=['numero_contrat']),
        models.Index(fields=['code_matricule']),
    ]



# ======================= BÉNÉFICIAIRE =======================
class Beneficiaire(models.Model):
    TYPE_FILIATION_CHOICES = [
        ('conjoint', 'Conjoint'),
        ('enfant', 'Enfant'),
    ]

    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]

    mutualiste = models.ForeignKey(
        Mutualiste, 
        on_delete=models.CASCADE, 
        related_name="beneficiaires",
        help_text="Mutualiste auquel appartient ce bénéficiaire"
    )
    nom = models.CharField(
        max_length=100, 
        help_text="Nom du bénéficiaire"
    )
    prenom = models.CharField(
        max_length=100, 
        help_text="Prénom du bénéficiaire"
    )
    photo = models.ImageField(
        upload_to='mutualistes/ayants droits/photos/', 
        null=True, 
        blank=True, 
        help_text="Photo du mutualiste", default='default/photo.png'
    )
    type_filiation = models.CharField(
        max_length=50, 
        choices=TYPE_FILIATION_CHOICES, 
        help_text="Lien de parenté avec le mutualiste"
    )
    date_naissance = models.DateField(
        help_text="Date de naissance du bénéficiaire"
    )
    sexe = models.CharField(
        max_length=10, 
        choices=SEXE_CHOICES, 
        help_text="Sexe du bénéficiaire"
    )
    code_matricule = models.CharField(
        max_length=9, 
        unique=True, 
        null=True, 
        editable=False, 
        help_text="Code matricule généré automatiquement"
    )
    statut = models.BooleanField(
        default=True, 
        help_text="Statut actif ou inactif"
    )
    date_adhesion = models.DateField(
        auto_now_add=True, null=True,
        help_text="Date d'adhésion à l'assurance beneficiaires"
    )
    observations = models.CharField(max_length=255,default="R.A.S")
    telephone = models.CharField(
        max_length=15, 
        null=True, 
        blank=True, 
        help_text="Numéro de téléphone de l'utilisateur"
    )
    def save(self, *args, **kwargs):
        # Génération automatique des identifiants


        if not self.code_matricule:
            if self.date_adhesion:
                self.code_matricule = f"{self.date_adhesion.year}{uuid.uuid4().hex[:5].upper()}ML"
            else:
                self.code_matricule = f"0000{uuid.uuid4().hex[:5].upper()}ML"
            
            # On s'assure que `code_matricule` respecte max_length=9
            self.code_matricule = self.code_matricule[:9]

        super().save(*args, **kwargs)
        
    def changer_code_matricule(self):
        """
        Change le code matricule en cas de perte ou vol de la carte.
        """
        self.code_matricule = self.generer_code_matricule()
        self.save()
        
    @property
    def age(self):
        """
        Calcule l'âge actuel du bénéficiaire.
        """
        today = date.today()
        age = today.year - self.date_naissance.year
        if (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day):
            age -= 1
        return age

    def __str__(self):
        return f"{self.nom} {self.prenom} - {self.type_filiation} ({self.age} ans)"

    def statistiques_prestations(self):
        """
        Retourne un résumé des statistiques importantes liées aux prestations
        ayant le statut de validation égal à 1.
        """
        stats = self.prises_en_charge.filter(prestations__statut_validation=1).aggregate(
            total_prestations=Count('prestations'),
            montant_total=Sum('prestations__montant_total'),
            part_mutuelle=Sum('prestations__montant_pris_en_charge'),
            part_mutualiste=Sum('prestations__montant_moderateur')
        )
        return {
            "total_prestations": stats['total_prestations'] or 0,
            "montant_total": stats['montant_total'] or 0.0,
            "part_mutuelle": stats['part_mutuelle'] or 0.0,
            "part_mutualiste": stats['part_mutualiste'] or 0.0,
    }
        
    class Meta:
        verbose_name = "Bénéficiaire"
        verbose_name_plural = "Bénéficiaires"
        ordering = ['nom', 'prenom']



class Mutualisteliste(models.Model):
    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]
    TYPE_FILIATION_CHOICES = [
        ('adherent', 'Adhérent'),
        ('conjoint', 'Conjoint'),
        ('enfant', 'Enfant'),
    ]

    # Clé primaire unique pour chaque mutualiste ou bénéficiaire
    numero_contrat = models.CharField(
        max_length=12, editable=False,
        help_text="Numéro unique du contrat d'assurance généré automatiquement"
    )
    code_matricule = models.CharField(
        max_length=9, unique=True, editable=False,
        help_text="Code matricule unique généré automatiquement"
    )

    # Informations personnelles
    photo = models.ImageField(
        upload_to='mutualistes/photos/', null=True, blank=True,
        help_text="Photo du mutualiste", default='default/photo.png'
    )
    nom = models.CharField(max_length=100, help_text="Nom", null=True)
    prenom = models.CharField(max_length=100, help_text="Prénom", null=True)
    date_naissance = models.DateField(help_text="Date de naissance")
    sexe = models.CharField(
        max_length=10, choices=SEXE_CHOICES, null=True, help_text="Sexe"
    )
    mutualiste = models.ForeignKey(
        Mutualiste, 
        on_delete=models.CASCADE, 
        null=True,
        related_name="listemut",
        help_text="Le mutualiste ayant cette"
    )
    beneficiaire = models.ForeignKey(
        Beneficiaire,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="listemutb",
        help_text="Bénéficiaire concerné, s'il ne s'agit pas du mutualiste"
    )

    # Type de filiation (Adhérent, Conjoint, Enfant)
    type_filiation = models.CharField(
        max_length=50, choices=TYPE_FILIATION_CHOICES, help_text="Lien de parenté" 
    )

    # Régime d'assurance et adhésion
    regime = models.ForeignKey(
        Regime, on_delete=models.SET_NULL, null=True, related_name="mutualistesliste",
        help_text="Régime d'assurance liste associé"
    )
    groupe = models.ForeignKey(
        Groupe,  # Référence au modèle Groupe 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="diocèseliste"
    )

    date_adhesion = models.DateField(
        auto_now_add=True, help_text="Date d'adhésion"
    )
    statut = models.BooleanField(
        default=True, help_text="Statut actif ou inactif"
    )
    observations = models.CharField(
        max_length=255, default="R.A.S", help_text="Observations"
    )
    telephone = models.CharField(
        max_length=15, 
        null=True, 
        blank=True, 
        help_text="Numéro de téléphone de l'utilisateur"
    )

    ## -------------------- Propriétés et Méthodes -------------------- ##

    @property
    def age(self):
        """Calcule l'âge du mutualiste."""
        today = date.today()
        age = today.year - self.date_naissance.year
        if (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day):
            age -= 1
        return age

    @property
    def nombre_beneficiaires(self):
        """Retourne le nombre de bénéficiaires rattachés au mutualiste."""
        return self.beneficiaires.count()

    @property
    def dernier_dossier(self):
        """Retourne le dernier dossier de prise en charge pour ce mutualiste."""
        return self.prises_en_charge.order_by('-date_creation').first()

    @property
    def montant_total_prestations(self):
        """Calcule le montant total cumulé des prestations pour ce mutualiste."""
        return self.prises_en_charge.aggregate(
            montant_total=Sum('prestations__montant_total')
        )['montant_total'] or 0.0

    def statistiques_prestations(self):
        """Retourne un résumé des statistiques des prestations du mutualiste."""
        stats = self.prises_en_charge.aggregate(
            total_prestations=Count('prestations'),
            montant_total=Sum('prestations__montant_total'),
            part_mutuelle=Sum('prestations__part_mutuelle'),
            part_mutualiste=Sum('prestations__part_mutualiste')
        )
        return {
            "total_prestations": stats['total_prestations'] or 0,
            "montant_total": stats['montant_total'] or 0.0,
            "part_mutuelle": stats['part_mutuelle'] or 0.0,
            "part_mutualiste": stats['part_mutualiste'] or 0.0,
        }

    def clean(self):
        """Validation de la date de naissance."""
        if self.date_naissance > date.today():
            raise ValidationError("La date de naissance ne peut pas être dans le futur.")

    #def save(self, *args, **kwargs):
        """Génère un numéro de contrat et un code matricule si non définis."""
    #    if not self.numero_contrat:
    #        self.numero_contrat = str(uuid.uuid4().int)[:12]  # Numéro unique
    #    if not self.code_matricule:
    #        self.code_matricule = str(uuid.uuid4().int)[:9]  # Code matricule unique
    #    super().save(*args, **kwargs)

    def __str__(self):
        """Affichage sous forme : Contrat-Matricule - Nom Prénom"""
        return f"{self.numero_contrat}-{self.code_matricule} - {self.nom} {self.prenom}"

    class Meta:
        verbose_name = "Mutualiste"
        verbose_name_plural = "Mutualistes"
        ordering = ['numero_contrat']
        indexes = [
            models.Index(fields=['numero_contrat']),
            models.Index(fields=['code_matricule']),
        ]



class NaturePrestationSociale(models.Model):
    """
    Modèle représentant une prestation individuelle dans une demande de prestation sociale.
    """
    nature = models.CharField(
        max_length=100,
        help_text="Nature de la prestation (ex: Scolarité, Médicale, Logement)"
    )
    montant = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        help_text="Montant de la prestation"
    )

    def __str__(self):
        return f"{self.nature} - {self.montant} FCFA"
    
class PrestationSociale(models.Model):
    """
    Modèle représentant une demande de prestation sociale.
    """
    ETATS_PRESTATION = [
        ('soumis', 'Soumis'),
        ('validé', 'Validé'),
        ('payé', 'Payé'),
        ('rejeté', 'Rejeté'),
    ]

    mutualiste = models.ForeignKey(
        Mutualiste,
        on_delete=models.CASCADE,
        related_name="prestations_sociales",
        help_text="Mutualiste bénéficiant de la prestation"
    )
    prestation_sociale = models.ForeignKey(
        NaturePrestationSociale,
        on_delete=models.CASCADE,
        related_name="prestationsociale",
        help_text="Demande de prestation sociale associée"
    )
    etat = models.CharField(
        max_length=10,
        choices=ETATS_PRESTATION,
        default='soumis',
        help_text="État de la prestation sociale"
    )
    date_soumission = models.DateField(
        default=now,
        help_text="Date de soumission de la demande"
    )
    date_validation = models.DateField(
        null=True,
        blank=True,
        help_text="Date de validation de la demande"
    )
    date_paiement = models.DateField(
        null=True,
        blank=True,
        help_text="Date de paiement de la prestation"
    )
    justification = models.FileField(
        upload_to="justificatifs/",
        blank=True,
        null=True,
        help_text="Justification de la prestation sociale"
    )
    preuve_paiement = models.FileField(
        upload_to="preuves_paiement/",
        blank=True,
        null=True,
        help_text="Fichier justificatif du paiement"
    )

    def __str__(self):
        return f"Prestation Sociale #{self.id} - {self.mutualiste.nom} {self.mutualiste.prenoms}"


