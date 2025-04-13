# Exemple d'utilisation dans le système
# Vérification d'une prise en charge en pharmacie

from datetime import date, timedelta

from configurations.models import HistoriqueCodeMatricule
from mutualistes.models import Mutualiste

def est_prise_en_charge_valide(prise_en_charge):
    """
    Vérifie si une prise en charge est encore valide pour un régime donné
    """
    regime = prise_en_charge.mutualiste.regime
    duree_validite = regime.get_duree_validation_pharmacie()
    date_expiration = prise_en_charge.date_prise_en_charge + timedelta(days=duree_validite)
    return date.today() <= date_expiration


# ====================================================================
# Calcul des frais à charge du mutualiste
def calcul_frais_mutualiste(total_frais, regime):
    """
    Calcule les frais à charge du mutualiste en fonction du régime
    """
    taux_couverture = regime.get_taux_couverture()
    frais_pris_en_charge = (total_frais * taux_couverture) / 100
    frais_mutualiste = total_frais - frais_pris_en_charge

    # Appliquer un plafond si défini
    plafond = regime.get_plafond_annuel()
    if plafond and frais_pris_en_charge > plafond:
        frais_pris_en_charge = plafond
        frais_mutualiste = total_frais - frais_pris_en_charge

    return frais_mutualiste

# Fonctionnalité de changement du code matricule =======================
# Voici comment vous pouvez utiliser la méthode changer_code_matricule :
# Exemple d'utilisation
def remplacer_code_matricule(mutualiste_id):
    try:
        mutualiste = Mutualiste.objects.get(id=mutualiste_id)
        mutualiste.changer_code_matricule()
        return f"Le nouveau code matricule est : {mutualiste.code_matricule}"
    except Mutualiste.DoesNotExist:
        return "Mutualiste introuvable"

# Modification dans la méthode changer_code_matricule :==============
def changer_code_matricule(self):
    """
    Change le code matricule en cas de perte ou vol de la carte, en sauvegardant l'ancien code.
    """
    HistoriqueCodeMatricule.objects.create(
        mutualiste=self,
        ancien_code=self.code_matricule
    )
    self.code_matricule = self.generer_code_matricule()
    self.save()


# Vue pour Statistiques Globales ===================
# Pour afficher ces informations dans une vue ou un tableau de bord :
# Dans le template mutualiste_dashboard.html, vous pouvez afficher les statistiques.
from django.shortcuts import render
from .models import Mutualiste

def tableau_de_bord_mutualiste(request, mutualiste_id):
    mutualiste = Mutualiste.objects.get(id=mutualiste_id)
    statistiques = mutualiste.statistiques_prestations()
    context = {
        "mutualiste": mutualiste,
        "nombre_prises_en_charge": mutualiste.nombre_prises_en_charge,
        "montant_total_prestations": mutualiste.montant_total_prestations,
        "dernier_dossier": mutualiste.dernier_dossier,
        "statistiques": statistiques,
    }
    return render(request, "mutualiste_dashboard.html", context)

# Nombre total de prises en charge par mutualiste ========================
from django.db.models import Count

def total_prises_en_charge_par_mutualiste():
    return Mutualiste.objects.annotate(
        nombre_prises_en_charge=Count('priseencharge')
    ).values('utilisateur__username', 'nombre_prises_en_charge')


# Montant total des prestations médicales et pharmaceutiques ========
from django.db.models import Sum

def montant_total_prestations():
    prestations_medicales = PrestationMedicale.objects.aggregate(
        total_medical=Sum('montant')
    )
    prestations_pharmaceutiques = PrestationPharmacie.objects.aggregate(
        total_pharma=Sum('montant_total')
    )
    return {
        "total_medical": prestations_medicales['total_medical'] or 0,
        "total_pharmaceutique": prestations_pharmaceutiques['total_pharma'] or 0,
        "total_general": (prestations_medicales['total_medical'] or 0) + 
                         (prestations_pharmaceutiques['total_pharma'] or 0)
    }

# Nombre d'ordonnances renouvelées =======================
from django.db.models import Count

def nombre_ordonnances_renouvelees():
    return Prescription.objects.filter(renouvelee=True).count()


# Top 5 des médicaments les plus prescrits =======================
def top_medicaments_prescrits():
    return Medicament.objects.annotate(
        nombre_prescriptions=Count('prescriptions')
    ).order_by('-nombre_prescriptions')[:5].values('nom', 'nombre_prescriptions')


# =======================


# =======================