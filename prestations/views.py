import calendar
from datetime import date, timedelta, timezone
from django.forms import ValidationError, formset_factory, modelformset_factory
from django.shortcuts import render, get_object_or_404, redirect

from facturations.models import Facture
from utilisateurs.models import Utilisateur
from .models import ExamenMedical, Hospitalisation, ListeDesPrestations, Medicament, NaturePriseEnCharge, Prescription, PrestationLunetterie, PriseEnCharge, Prestation
from .forms import ExamenMedicalForm, ExamenValidationForm, HospitalisationValidationForm, ListeDesPrestationsForm, MedicamentForm, OptiqueValidationForm, PrescriptionForm, PrestationForm,ExamenMedicalFormSet,MedicamentPrescrisFormSet
import pandas as pd
from django.contrib import messages
from django.http import HttpRequest
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from mutualistes.models import Mutualiste, Beneficiaire, Mutualisteliste
from centres.models import  CentreSante, CentreSantePrestation, MedecinTraitant
from django.shortcuts import render, get_object_or_404
from .models import PriseEnCharge
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_protect
from django.db.models import Sum
# ===============================================  LISTE DES PRESTATIONS ======================================================================================================
# Liste des prestations
def prestation_list(request):
    prestations = ListeDesPrestations.objects.all()
    return render(request, 'backoffice/prestations/prestation_list.html', {'prestations': prestations})

# Détails d'une prestation 
def prestation_detail(request, pk):
    centre= get_object_or_404(CentreSante,pk=pk)
    prestations = CentreSantePrestation.objects.filter(centre_sante=pk)
    ordonnances = PrestationPharmacie.objects.filter(centre_sante=pk)
    acteprestations = Prestation.objects.filter(centre_sante=pk, statut_validation=True)
    acces = Utilisateur.objects.filter(centre_sante=pk) 
    return render(request, 'backoffice/prestations/prestation_detail.html', {'centre':centre,'prestations': prestations,'acteprestations':acteprestations,'acces':acces,'ordonnances':ordonnances})  

# Ajouter une prestation
def prestation_create(request):
    if request.method == 'POST':
        form = ListeDesPrestationsForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('prestation_list')
    else:
        form = ListeDesPrestationsForm()
    return render(request, 'backoffice/prestations/prestation_form.html', {'form': form}) 

# Modifier une prestation
def prestation_update(request, pk):
    prestation = get_object_or_404(ListeDesPrestations, pk=pk)
    if request.method == 'POST':
        form = ListeDesPrestationsForm(request.POST, instance=prestation)
        if form.is_valid():
            form.save()
            return redirect('prestation_list')
    else:
        form = ListeDesPrestationsForm(instance=prestation)
    return render(request, 'backoffice/prestations/prestation_form.html', {'form': form})

# Supprimer une prestation
def prestation_delete(request, pk):
    prestation = get_object_or_404(ListeDesPrestations, pk=pk)
    if request.method == 'POST':
        prestation.delete()
        return redirect('prestation_list')
    return render(request, 'backoffice/prestations/prestation_confirm_delete.html', {'prestation': prestation})

# importer_prestations
def importer_prestations(request):
    if request.method == 'POST':
        fichier_excel = request.FILES.get('fichier_excel')
        
        if not fichier_excel:
            messages.error(request, "Veuillez sélectionner un fichier Excel.")
            return redirect('importer_prestations')
        
        try:
            # Lire le fichier Excel avec pandas
            df = pd.read_excel(fichier_excel)

            # Vérifier que le fichier contient les colonnes nécessaires
            colonnes_requises = ['nom', 'description', 'categorie', 'tarif_standard', 'actif', 'soumis_a_validation']
            if not all(colonne in df.columns for colonne in colonnes_requises):
                messages.error(request, "Le fichier Excel doit contenir les colonnes suivantes : " + ", ".join(colonnes_requises))
                return redirect('importer_prestations')

            # Parcourir les lignes et créer des objets `ListeDesPrestations`
            for _, row in df.iterrows():
                ListeDesPrestations.objects.create(
                    nom=row['nom'],
                    description=row.get('description', ''),
                    categorie=row['categorie'],
                    tarif_standard=row['tarif_standard'],
                    actif=row['actif'],
                    soumis_a_validation=row['soumis_a_validation']
                )
            
            messages.success(request, "Les prestations ont été importées avec succès !")
            return redirect('prestation_list')

        except Exception as e:
            messages.error(request, f"Erreur lors de l'importation du fichier : {e}")
            return redirect('importer_prestations')

    return render(request, 'backoffice/prestations/importer_prestations.html')
#  ----------------------------------------------------------------------------------------------------------------------

# ============================================================ RECHERCHER POUR UNE PRISE EN CHARGE DES CONSULTATIONS ===============================================
def demarrer_prise_en_charge(request):
    return render(request, 'frontoffice/priseencharge/modal.html')

from django.http import JsonResponse
def valider_matricule(request):
    matricule = request.GET.get('matricule')

    if not matricule:
        return JsonResponse({"status": "error", "message": "Le matricule est requis."}, status=400)

    try:
        print(f"🔍 Matricule recherché : {matricule}")

        # Vérifier si c'est un Bénéficiaire EN PREMIER
        beneficiaire = Beneficiaire.objects.filter(code_matricule=matricule).first()
        if beneficiaire:
            print(f"✅ Bénéficiaire trouvé : {beneficiaire.nom} {beneficiaire.prenom} (ID: {beneficiaire.id})")
            return JsonResponse({
                "status": "success",
                "type": "beneficiaire",
                "data": {
                    'id': beneficiaire.id,
                    "nom": beneficiaire.nom,
                    "prenom": beneficiaire.prenom,
                    "age": beneficiaire.age,
                    "photo": beneficiaire.photo.url if beneficiaire.photo else None,
                }
            })

        # Vérifier si c'est un Mutualiste après
        mutualiste = Mutualiste.objects.filter(code_matricule=matricule).first()
        if mutualiste:
            print(f"✅ Mutualiste trouvé : {mutualiste.nom} {mutualiste.prenom} (ID: {mutualiste.id})")
            return JsonResponse({
                "status": "success",
                "type": "mutualiste",
                "data": {
                    'id': mutualiste.id,
                    "nom": mutualiste.nom,
                    "prenom": mutualiste.prenom,
                    "age": mutualiste.age,
                    "photo": mutualiste.photo.url if mutualiste.photo else None,
                }
            })

        print("❌ Aucun mutualiste ou bénéficiaire trouvé.")
        return JsonResponse({"status": "error", "message": "Matricule non trouvé."}, status=404)

    except Exception as e:
        print(f"❌ Erreur API : {str(e)}")
        return JsonResponse({"status": "error", "message": f"Une erreur est survenue : {str(e)}"}, status=500)



# ============================================================ AJOUTER UNE PRISE EN CHARGE DES CONSULTATIONS ===============================================
def calculer_montant_total(mutualiste, prestation):
    """
    Calculer le montant total de la prestation. Cela prend le tarif de la prestation 
    et le multiplie par le taux de couverture de la mutuelle, tout en respectant le plafond 
    annuel de couverture.
    """
    # Vérifier que le tarif de la prestation n'est pas None
    if prestation.tarif_personnalise is None:
        raise ValueError("Le tarif de la prestation ne peut pas être None.")
    
    # Vérifier que le plafond annuel est bien défini
    plafond_annuel = mutualiste.regime.plafond_annuel_couverture if mutualiste.regime.plafond_annuel_couverture else None
    
    # Calculer le montant total de la prestation
    montant_total = prestation.tarif_personnalise
    
    # Si un plafond est défini et que le montant total dépasse ce plafond, ajuster
    if plafond_annuel and montant_total > plafond_annuel:
        montant_total = plafond_annuel

    return montant_total


def calculer_montant_pris_en_charge(mutualiste, prestation):
    """
    Calculer le montant pris en charge par la mutuelle. Le montant pris en charge est 
    basé sur le tarif de la prestation multiplié par le taux de couverture de la mutuelle.
    """
    # Vérifier que le tarif de la prestation n'est pas None
    if prestation.tarif_personnalise is None:
        raise ValueError("Le tarif de la prestation ne peut pas être None.")
    
    # Vérifier que le taux de couverture est valide
    taux_couverture = mutualiste.regime.taux_couverture if mutualiste.regime.taux_couverture is not None else 0
    if taux_couverture == 0:
        raise ValueError("Le taux de couverture de la mutuelle est invalide ou manquant.")
    
    # Calcul du montant pris en charge par la mutuelle
    montant_pris_en_charge = prestation.tarif_personnalise * (taux_couverture / 100)  # Conversion en pourcentage

    # Appliquer le plafond annuel de couverture
    plafond_annuel = mutualiste.regime.plafond_annuel_couverture if mutualiste.regime.plafond_annuel_couverture else None
    if plafond_annuel:
        montant_pris_en_charge = min(montant_pris_en_charge, plafond_annuel)

    return montant_pris_en_charge



# Calculer la durée en jours, et non pas une date
def calculer_duree_validite(mutualiste):
    """
    Calculer la durée de validité en jours de la prestation
    en fonction de la mutuelle du mutualiste.
    """
    # Nombre de jours de validité de la mutuelle pour une consultation
    duree_validation = mutualiste.regime.duree_validation_consultation
    
    return duree_validation

# Calculer la durée en jours, et non pas une date
def calculer_duree_validiteoptique(mutualiste):
    """
    Calculer la durée de validité en jours de la prestation
    en fonction de la mutuelle du mutualiste.
    """
    # Nombre de jours de validité de la mutuelle pour une consultation
    duree_validation = mutualiste.regime.duree_validation_optique
    
    return duree_validation

    

def ajouter_prestations(request: HttpRequest, id: int):
    mutualiste = get_object_or_404(Mutualiste, id=id)
    # mutualistet = get_object_or_404(Mutualisteliste, id=id)
    nature = get_object_or_404(NaturePriseEnCharge, nature='Médicale')

    # Récupérer la dernière prise en charge du mutualiste
    last_prise_en_charge = PriseEnCharge.objects.filter(mutualiste=mutualiste,nature=nature).order_by('-date_prise_en_charge').first()

    # Si une prise en charge est encore valide, rediriger vers sa page de détails
    if last_prise_en_charge and last_prise_en_charge.duree_validite > 0:
        return redirect('detail_prise_en_charge', prise_en_charge_id=last_prise_en_charge.id)

    # Vérifier que l'utilisateur a un centre de santé
    if not hasattr(request.user, 'centre_sante'):
        return redirect('error_page')  # Redirection vers une page d'erreur si nécessaire

    if request.method == "POST":
        print(request.POST)  # 🔍 Debug : Vérifier le contenu du POST
        
        prestation_id = request.POST.get('prestation')  # ID de la prestation sélectionnée
        medecin_id = request.POST.get('medecin')  # ID du médecin sélectionné
        description_clinique = request.POST.get('description_clinique')

        if prestation_id:  # Vérifier si une prestation a été sélectionnée
            prestation = get_object_or_404(
                CentreSantePrestation, 
                prestation=prestation_id, 
                centre_sante=request.user.centre_sante
            )
            medecin = get_object_or_404(MedecinTraitant, id=medecin_id)  # Vérifier l'existence du médecin
            
            duree_validite = calculer_duree_validite(mutualiste)  # Calcul de la durée de validité

            # Création de la prise en charge
            prise_en_charge = PriseEnCharge.objects.create(
                mutualiste=mutualiste,
                medecin_traitant=medecin,
                centre=request.user.centre_sante,
                date_prise_en_charge=date.today(),
                duree_validite=duree_validite,
                nature=nature
            )

            # Calcul du montant selon la logique métier
            montant_total = calculer_montant_total(mutualiste, prestation)
            montant_pris_en_charge = calculer_montant_pris_en_charge(mutualiste, prestation)
            montant_moderateur = montant_total - montant_pris_en_charge  

            # Création de la prestation avec validation automatique
            Prestation.objects.create(
                prise_en_charge=prise_en_charge,
                centre_sante=request.user.centre_sante,
                prestation=prestation.prestation,
                medecin_traitant=medecin,
                montant_total=montant_total,
                montant_pris_en_charge=montant_pris_en_charge,
                montant_moderateur=montant_moderateur,
                tiers_payant=True,
                description=description_clinique,
                statut_validation=True,
                date_validation=date.today()
            )
            
            # Gestion de la facture du mois
            #mois_actuel = now().month
            #annee_actuelle = now().year
            #facture, created = Facture.objects.get_or_create(
            #    centre=request.user.centre_sante,
            #    defaults={
            #        'total_mutualiste': 0,
            #        'total_mutuelle': 0,
            #        'total_general': 0
            #    }
            #) 
            mois_actuel = now().month
            annee_actuelle = now().year
            dernier_jour_du_mois = calendar.monthrange(annee_actuelle, mois_actuel)[1]
            # 📌 Vérifier si une facture existe pour ce centre et ce mois, sinon la créer
            facture, created = Facture.objects.get_or_create(
                centre=request.user.centre_sante,
                numero_facture=f"{mois_actuel:02}{annee_actuelle}",  # 🔹 Clé unique pour le mois
                defaults={  # 🔹 Valeurs si la facture est créée
                    'total_mutualiste': 0,
                    'total_mutuelle': 0,
                    'total_general': 0,
                    'date_debut': f"{annee_actuelle}-{mois_actuel:02}-01",
                    'date_fin': f"{annee_actuelle}-{mois_actuel:02}-{dernier_jour_du_mois}"
                }
            )

            # 📝 Mettre à jour les montants de la facture
            facture.total_mutualiste += montant_moderateur
            facture.total_mutuelle += montant_pris_en_charge
            facture.total_general = facture.total_mutualiste + facture.total_mutuelle
            facture.save()

            # Rediriger vers la page de détail de la prise en charge nouvellement créée
            return redirect('detail_prise_en_charge', prise_en_charge_id=prise_en_charge.id)

    # Si c'est une requête GET, afficher le formulaire avec les prestations et médecins disponibles
    prestations = CentreSantePrestation.objects.filter(
        centre_sante=request.user.centre_sante,
        prestation__categorie="consultation"
    )
    medecins = MedecinTraitant.objects.filter(
        centre_sante=request.user.centre_sante
    )

    return render(request, 'frontoffice/priseencharge/ajouter_prestations.html', {
        'mutualiste': mutualiste,
        'prestations': prestations,
        'medecins': medecins
    })
    
def ajouter_prestations_beneficiaire(request: HttpRequest, id: int):
    mutualiste = get_object_or_404(Beneficiaire, id=id)
    # mutualistet = get_object_or_404(Mutualisteliste, id=id)
    nature = get_object_or_404(NaturePriseEnCharge, nature='Médicale')

    # Récupérer la dernière prise en charge du mutualiste
    last_prise_en_charge = PriseEnCharge.objects.filter(beneficiaire=mutualiste,nature=nature).order_by('-date_prise_en_charge').first()

    # Si une prise en charge est encore valide, rediriger vers sa page de détails
    if last_prise_en_charge and last_prise_en_charge.duree_validite > 0:
        return redirect('detail_prise_en_charge', prise_en_charge_id=last_prise_en_charge.id)

    # Vérifier que l'utilisateur a un centre de santé
    if not hasattr(request.user, 'centre_sante'):
        return redirect('error_page')  # Redirection vers une page d'erreur si nécessaire

    if request.method == "POST":
        print(request.POST)  # 🔍 Debug : Vérifier le contenu du POST
        
        prestation_id = request.POST.get('prestation')  # ID de la prestation sélectionnée
        medecin_id = request.POST.get('medecin')  # ID du médecin sélectionné
        description_clinique = request.POST.get('description_clinique')

        if prestation_id:  # Vérifier si une prestation a été sélectionnée
            prestation = get_object_or_404(
                CentreSantePrestation, 
                prestation=prestation_id, 
                centre_sante=request.user.centre_sante
            )
            medecin = get_object_or_404(MedecinTraitant, id=medecin_id)  # Vérifier l'existence du médecin
            
            duree_validite = calculer_duree_validite(mutualiste.mutualiste)  # Calcul de la durée de validité

            # Création de la prise en charge
            prise_en_charge = PriseEnCharge.objects.create(
                mutualiste=mutualiste.mutualiste,
                beneficiaire=mutualiste,
                medecin_traitant=medecin,
                centre=request.user.centre_sante,
                date_prise_en_charge=date.today(),
                duree_validite=duree_validite,
                nature=nature
            )

            # Calcul du montant selon la logique métier
            montant_total = calculer_montant_total(mutualiste.mutualiste, prestation)
            montant_pris_en_charge = calculer_montant_pris_en_charge(mutualiste.mutualiste, prestation)
            montant_moderateur = montant_total - montant_pris_en_charge  

            # Création de la prestation avec validation automatique
            Prestation.objects.create(
                prise_en_charge=prise_en_charge,
                centre_sante=request.user.centre_sante,
                prestation=prestation.prestation,
                medecin_traitant=medecin,
                montant_total=montant_total,
                montant_pris_en_charge=montant_pris_en_charge,
                montant_moderateur=montant_moderateur,
                tiers_payant=True,
                description=description_clinique,
                statut_validation=True,
                date_validation=date.today()
            )
            
            # Gestion de la facture du mois get_or_
            mois_actuel = now().month
            annee_actuelle = now().year
            dernier_jour_du_mois = calendar.monthrange(annee_actuelle, mois_actuel)[1]
            # 📌 Vérifier si une facture existe pour ce centre et ce mois, sinon la créer
            facture, created = Facture.objects.get_or_create(
                centre=request.user.centre_sante,
                numero_facture=f"{mois_actuel:02}{annee_actuelle}",  # 🔹 Clé unique pour le mois
                defaults={  # 🔹 Valeurs si la facture est créée
                    'total_mutualiste': 0,
                    'total_mutuelle': 0,
                    'total_general': 0,
                    'date_debut': f"{annee_actuelle}-{mois_actuel:02}-01",
                    'date_fin': f"{annee_actuelle}-{mois_actuel:02}-{dernier_jour_du_mois}"
                }
            )

            # 📝 Mettre à jour les montants de la facture
            facture.total_mutualiste += montant_moderateur
            facture.total_mutuelle += montant_pris_en_charge
            facture.total_general = facture.total_mutualiste + facture.total_mutuelle
            facture.save()


            # Rediriger vers la page de détail de la prise en charge nouvellement créée
            return redirect('detail_prise_en_charge', prise_en_charge_id=prise_en_charge.id)

    # Si c'est une requête GET, afficher le formulaire avec les prestations et médecins disponibles
    prestations = CentreSantePrestation.objects.filter(
        centre_sante=request.user.centre_sante,
        prestation__categorie="consultation"
    )
    medecins = MedecinTraitant.objects.filter(
        centre_sante=request.user.centre_sante
    )

    return render(request, 'frontoffice/priseencharge/ajouter_prestations.html', {
        'mutualiste': mutualiste,
        'prestations': prestations,
        'medecins': medecins
    })

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
import tempfile
from django.utils.timezone import now
from .models import PriseEnCharge, Prestation  # Importation des modèles

def telecharger_prise_en_charge_pdf(request, id):
    # Récupération de la prise en charge et des prestations associées
    prise_en_charge = get_object_or_404(PriseEnCharge, id=id)
    prestations = Prestation.objects.filter(prise_en_charge=prise_en_charge)

    # Calcul des totaux
    total_prestations = sum(prestation.montant_total for prestation in prestations)
    total_part_mutuelle = sum(prestation.montant_pris_en_charge for prestation in prestations)
    total_part_mutualiste = sum(prestation.montant_moderateur for prestation in prestations)

    # Données supplémentaires
    mutuelle_logo = request.build_absolute_uri('/media/backoffice/img/logo.png')  # Assurez-vous que le logo est dans le dossier MEDIA
    nom_mutuelle = "Mutuelle Santé Plus"  # Change avec le vrai nom de ta mutuelle
    date_impression = now().strftime("%d/%m/%Y à %H:%M")  # Format date

    # Contexte pour le template
    context = {
        "prise_en_charge": prise_en_charge,
        "prestations": prestations,
        "totalPrestations": total_prestations,
        "totalPartMutuelle": total_part_mutuelle,
        "totalPartMutualiste": total_part_mutualiste,
        "mutuelle_logo": mutuelle_logo,
        "nom_mutuelle": nom_mutuelle,
        "date_impression": date_impression
    }

    # Rendu du template HTML
    html_string = render_to_string('frontoffice/priseencharge/pdf_templatelogo.html', context)

    # Génération du PDF temporaire
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Prise_en_Charge_{prise_en_charge.id}.pdf"'

    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        HTML(string=html_string).write_pdf(temp_file.name)
        temp_file.seek(0)
        response.write(temp_file.read())

    return response


# ============================================================ UNE PRISE EN CHARGE OPTIQUE ===============================================
def ajouter_prestationsoptique(request: HttpRequest, id: int):
    mutualiste = get_object_or_404(Mutualiste, id=id)
    nature = get_object_or_404(NaturePriseEnCharge, nature='Optique')

    # Récupérer la dernière prise en charge du mutualiste
    last_prise_en_charge = PriseEnCharge.objects.filter(mutualiste=mutualiste,nature=nature).order_by('-date_prise_en_charge').first()

    # Si une prise en charge est encore valide, rediriger vers sa page de détails
    if last_prise_en_charge and last_prise_en_charge.duree_validite > 0:
        return redirect('detail_prise_en_chargeoptique', prise_en_charge_id=last_prise_en_charge.id)

    # Vérifier que l'utilisateur a un centre de santé
    if not hasattr(request.user, 'centre_sante'):
        return redirect('error_page')  # Redirection vers une page d'erreur si nécessaire

    if request.method == "POST":
        print(request.POST)  # 🔍 Debug : Vérifier le contenu du POST
        
        prestation_id = request.POST.get('prestation')  # ID de la prestation sélectionnée
        medecin_id = request.POST.get('medecin')  # ID du médecin sélectionné
        description_clinique = request.POST.get('description_clinique')
        fichier_hospitalisation = request.FILES.get('fichier_hospitalisation')  # Récupérer le fichier

        if prestation_id:  # Vérifier si une prestation a été sélectionnée
            prestation = get_object_or_404(
                CentreSantePrestation, 
                prestation=prestation_id, 
                centre_sante=request.user.centre_sante
            )
            medecin = get_object_or_404(MedecinTraitant, id=medecin_id)  # Vérifier l'existence du médecin
                        

            # Création de la prestation avec validation automatique
            PrestationLunetterie.objects.create(
                mutualiste=mutualiste,
                centre_sante=request.user.centre_sante,
                prestation=prestation.prestation,
                medecin_traitant=medecin,
                montant_total=prestation.tarif_personnalise,
                forfait_verres_et_montures=prestation.tarif_personnalise,
                description=description_clinique,
                statut=PrestationLunetterie.StatutOptique.EN_ATTENTE,
                date_prestation=date.today(),
                fichier_resultat=fichier_hospitalisation                
            )
            
            # Rediriger vers la page de détail de la prise en charge nouvellement créée
            return redirect('dashboard_optique')

    # Si c'est une requête GET, afficher le formulaire avec les prestations et médecins disponibles
    prestations = CentreSantePrestation.objects.filter(
        centre_sante=request.user.centre_sante,
        prestation__categorie="optique"
    )
    medecins = MedecinTraitant.objects.filter(
        centre_sante=request.user.centre_sante
    )

    return render(request, 'frontoffice/priseencharge/ajouter_prestationsoptique.html', {
        'mutualiste': mutualiste,
        'prestations': prestations,
        'medecins': medecins
    })
    
def ajouter_prestationsoptiquebeneficiaire(request: HttpRequest, id: int):
    mutualiste = get_object_or_404(Beneficiaire, id=id)
    nature = get_object_or_404(NaturePriseEnCharge, nature='Optique')

    # Récupérer la dernière prise en charge du mutualiste
    last_prise_en_charge = PriseEnCharge.objects.filter(beneficiaire=mutualiste,nature=nature).order_by('-date_prise_en_charge').first()

    # Si une prise en charge est encore valide, rediriger vers sa page de détails
    if last_prise_en_charge and last_prise_en_charge.duree_validite > 0:
        return redirect('detail_prise_en_chargeoptique', prise_en_charge_id=last_prise_en_charge.id)

    # Vérifier que l'utilisateur a un centre de santé
    if not hasattr(request.user, 'centre_sante'):
        return redirect('error_page')  # Redirection vers une page d'erreur si nécessaire

    if request.method == "POST":
        print(request.POST)  # 🔍 Debug : Vérifier le contenu du POST
        
        prestation_id = request.POST.get('prestation')  # ID de la prestation sélectionnée
        medecin_id = request.POST.get('medecin')  # ID du médecin sélectionné
        description_clinique = request.POST.get('description_clinique')
        fichier_hospitalisation = request.FILES.get('fichier_hospitalisation')  # Récupérer le fichier

        if prestation_id:  # Vérifier si une prestation a été sélectionnée
            prestation = get_object_or_404(
                CentreSantePrestation, 
                prestation=prestation_id, 
                centre_sante=request.user.centre_sante
            )
            medecin = get_object_or_404(MedecinTraitant, id=medecin_id)  # Vérifier l'existence du médecin
                        
 
            # Création de la prestation avec validation automatique
            PrestationLunetterie.objects.create(
                mutualiste=mutualiste.mutualiste,
                beneficiaire=mutualiste,
                centre_sante=request.user.centre_sante,
                prestation=prestation.prestation,
                medecin_traitant=medecin,
                montant_total=prestation.tarif_personnalise,
                forfait_verres_et_montures=prestation.tarif_personnalise,
                description=description_clinique,
                statut=PrestationLunetterie.StatutOptique.EN_ATTENTE,
                date_prestation=date.today(),
                fichier_resultat=fichier_hospitalisation                
            )
            
            # Rediriger vers la page de détail de la prise en charge nouvellement créée
            return redirect('dashboard_optique')

    # Si c'est une requête GET, afficher le formulaire avec les prestations et médecins disponibles
    prestations = CentreSantePrestation.objects.filter(
        centre_sante=request.user.centre_sante,
        prestation__categorie="optique"
    )
    medecins = MedecinTraitant.objects.filter(
        centre_sante=request.user.centre_sante
    )

    return render(request, 'frontoffice/priseencharge/ajouter_prestationsoptique.html', {
        'mutualiste': mutualiste,
        'prestations': prestations,
        'medecins': medecins
    })
    
# ============================================================ DETAIL UNE PRISE EN CHARGE  ===============================================
def detail_prise_en_charge(request, prise_en_charge_id): 
    prise_en_charge = get_object_or_404(PriseEnCharge, id=prise_en_charge_id)

    # Vous pouvez ajouter plus de logique pour afficher les prestations associées et autres informations pertinentes.
    prestations = Prestation.objects.filter(prise_en_charge=prise_en_charge,statut_validation=True)
    

    return render(request, 'frontoffice/priseencharge/detail_prise_en_charge.html', {
        'prise_en_charge': prise_en_charge,
        'prestations': prestations
    })
    
def detail_prise_en_chargeoptique(request, prise_en_charge_id):
    prise_en_charge = get_object_or_404(PriseEnCharge, id=prise_en_charge_id)

    # Vous pouvez ajouter plus de logique pour afficher les prestations associées et autres informations pertinentes.
    prestations = Prestation.objects.filter(prise_en_charge=prise_en_charge,statut_validation=True)
    

    return render(request, 'frontoffice/priseencharge/detail_prise_en_chargeoptque.html', {
        'prise_en_charge': prise_en_charge,
        'prestations': prestations
    })

# ============================================================ AJOUTER UNE PRISE EN CHARGE DES EXAMENS ===============================================
def ajouter_prestationsex(request, id):
    prise_en_charge = get_object_or_404(PriseEnCharge, id=id)
    mutualiste = prise_en_charge.mutualiste  # Mutualiste lié à la prise en charge

    # Utilisation de modelformset_factory pour gérer plusieurs examens
    ExamenMedicalFormSet = modelformset_factory(ExamenMedical, form=ExamenMedicalForm, extra=1, can_delete=False)

    if request.method == "POST":
        print("Données POST reçues :", request.POST)  # Debug
        print("Données FILES reçues :", request.FILES)  # Debug

        formset = ExamenMedicalFormSet(request.POST, request.FILES, queryset=ExamenMedical.objects.filter(prise_en_charge=prise_en_charge))

        if formset.is_valid():
            examens = formset.save(commit=False)  # Empêcher l'enregistrement immédiat

            examens_existants = ExamenMedical.objects.filter(prise_en_charge=prise_en_charge)
            examens_types_existants = set(examens_existants.values_list("type_examen_id", flat=True))

            erreurs = []  # Stocker les erreurs pour ne pas interrompre le processus

            for examen in examens:
                if examen.type_examen:  # Vérifie si le champ est rempli
                    if examen.type_examen_id in examens_types_existants:
                        erreurs.append(f"L'examen {examen.type_examen} est déjà ajouté.")
                    else:
                        # Assigner les informations nécessaires avant l'enregistrement
                        examen.prise_en_charge = prise_en_charge
                        examen.mutualiste = mutualiste
                        examen.centre_sante = request.user.centre_sante
                        examen.date_prescription = timezone.now()
                        examen.statut = ExamenMedical.StatutExamen.EN_ATTENTE
                        examen.save()

            if erreurs:
                for erreur in erreurs:
                    messages.error(request, erreur)

                return render(request, "frontoffice/priseencharge/ajouter_prestationsex.html", {
                    "prise_en_charge": prise_en_charge,
                    "formset": formset
                })

            messages.success(request, "Examens ajoutés avec succès !")
            return redirect('detail_prise_en_charge', prise_en_charge_id=prise_en_charge.id)

    else:
        formset = ExamenMedicalFormSet(queryset=ExamenMedical.objects.none())  # Formulaires vides

    return render(request, "frontoffice/priseencharge/ajouter_prestationsex.html", {
        "prise_en_charge": prise_en_charge,
        "formset": formset
    })


def ajouter_prestationsex_beneficiaire(request, id):
    prise_en_charge = get_object_or_404(PriseEnCharge, id=id)
    mutualiste = prise_en_charge.beneficiaire  # Mutualiste ou bénéficiaire concerné

    # Formset pour gérer plusieurs examens
    ExamenMedicalFormSet = modelformset_factory(ExamenMedical, form=ExamenMedicalForm, extra=1, can_delete=False)

    if request.method == "POST":
        print("Données POST reçues :", request.POST)  # Debugging
        print("Données FILES reçues :", request.FILES)  # Debugging

        formset = ExamenMedicalFormSet(request.POST, request.FILES, queryset=ExamenMedical.objects.filter(prise_en_charge=prise_en_charge))

        if formset.is_valid():
            examens = formset.save(commit=False)  # Ne pas enregistrer immédiatement

            examens_existants = ExamenMedical.objects.filter(prise_en_charge=prise_en_charge)
            examens_types_existants = set(examens_existants.values_list("type_examen_id", flat=True))

            erreurs = []  # Liste des erreurs pour éviter les retours précoces

            for examen in examens:
                if examen.type_examen:  # Vérifier si le champ est rempli
                    if examen.type_examen_id in examens_types_existants:
                        erreurs.append(f"L'examen {examen.type_examen} est déjà ajouté.")

                    else:
                        # Remplissage des champs avant enregistrement
                        examen.prise_en_charge = prise_en_charge
                        examen.mutualiste = mutualiste  # Correction ici, éviter `mutualiste.mutualiste`
                        examen.beneficiaire = mutualiste
                        examen.centre_sante = request.user.centre_sante
                        examen.date_prescription = timezone.now()
                        examen.statut = ExamenMedical.StatutExamen.EN_ATTENTE
                        examen.save()

            if erreurs:
                for erreur in erreurs:
                    messages.error(request, erreur)

                return render(request, "frontoffice/priseencharge/ajouter_prestationsex.html", {
                    "prise_en_charge": prise_en_charge,
                    "formset": formset
                })

            messages.success(request, "Examens ajoutés avec succès !")
            return redirect('detail_prise_en_charge', prise_en_charge_id=prise_en_charge.id)

    else:
        formset = ExamenMedicalFormSet(queryset=ExamenMedical.objects.none())  # Formulaires vides

    return render(request, "frontoffice/priseencharge/ajouter_prestationsex.html", {
        "prise_en_charge": prise_en_charge,
        "formset": formset
    })


# ============================================================ PRESTATION HOSPITALISATION =============================================================
def ajouter_prestationshospi(request: HttpRequest, id: int):
    mutualiste = get_object_or_404(Mutualiste, id=id)

    # Récupérer la dernière prise en charge du mutualiste
    last_prise_en_charge = PriseEnCharge.objects.filter(mutualiste=mutualiste).order_by('-date_prise_en_charge').first()

    prestations = []  # Initialisation de la variable prestations

    if last_prise_en_charge and last_prise_en_charge.duree_validite > 0:
        if request.method == "POST":
            # Debugging pour afficher les données du formulaire
            print(request.POST)
            print(f"Centre santé utilisateur: {request.user.centre_sante}")

            prestation_id = request.POST.get('prestation')
            medecin_id = request.POST.get('medecin')
            motif_hospitalisation = request.POST.get('motif_hospitalisation')
            date_sortie_str = request.POST.get('date_sortie')
            duree_validite = int(request.POST.get('duree_validite', 0))  # Convertir en int
            fichier_hospitalisation = request.FILES.get('fichier_hospitalisation')  # Récupérer le fichier

            if prestation_id and medecin_id:
                try:
                    # Récupération de la prestation et du médecin
                    prestation = get_object_or_404(CentreSantePrestation, prestation=prestation_id, centre_sante=request.user.centre_sante)
                    medecin = get_object_or_404(MedecinTraitant, id=medecin_id)

                    # Calculer le montant pris en charge
                    montant_pris_en_charge = calculer_montant_pris_en_charge(mutualiste, prestation)

                    # Calculer la date de sortie
                    date_sortie = date.today() + timedelta(days=duree_validite)
                    
                    # Vérifier s'il existe déjà une hospitalisation pour cette prise en charge
                    hospitalisation_existante = Hospitalisation.objects.filter(
                        prise_en_charge=last_prise_en_charge
                    ).exclude(statut_prise_en_charge=Hospitalisation.StatutPriseEnCharge.REFUSÉE).exists()

                    if hospitalisation_existante:
                        return render(request, 'frontoffice/priseencharge/ajouter_prestationshospi.html', {
                            'mutualiste': mutualiste,
                            'prestations': prestations,
                            'medecins': medecins,
                            'error_message': 'Une hospitalisation existe déjà pour cette prise en charge.'
                        })

                    # Création de l'hospitalisation
                    hospi = Hospitalisation.objects.create(
                        prise_en_charge=last_prise_en_charge,
                        mutualiste=mutualiste,
                        centre_sante=request.user.centre_sante,
                        date_sortie=date_sortie,
                        motif_hospitalisation=motif_hospitalisation,
                        fichier_hospitalisation=fichier_hospitalisation,
                        statut_prise_en_charge=Hospitalisation.StatutPriseEnCharge.EN_ATTENTE,
                        montant_prise_en_charge=montant_pris_en_charge,
                        duree_validite=duree_validite
                    )

                    # Calculer le montant total et le montant pris en charge
                    montant_total = calculer_montant_total(mutualiste, prestation)

                    # Création de la prestation
                    prestation_obj=Prestation.objects.create(
                        prise_en_charge=last_prise_en_charge,
                        centre_sante=request.user.centre_sante,
                        prestation=prestation.prestation,
                        medecin_traitant=medecin,
                        montant_total=montant_total,
                        montant_pris_en_charge=montant_pris_en_charge,
                        montant_moderateur=montant_total - montant_pris_en_charge,
                        tiers_payant=True,
                        description=motif_hospitalisation,
                        statut_validation=False,
                        date_validation=date.today()
                    )
                    
                    # Ajout de la prestation à l'hospitalisation
                    hospi.prestations.add(prestation_obj)

                    messages.success(request, "La demande d'hospitalisation a été ajoutée avec succès !")
                    return redirect('detail_prise_en_charge', prise_en_charge_id=last_prise_en_charge.id)

                except Exception as e:
                    # Si une erreur se produit, renvoyer un message d'erreur
                    print(f"Erreur lors de la création de la prestation: {e}")
                    return render(request, 'frontoffice/priseencharge/ajouter_prestationshospi.html', {
                        'mutualiste': mutualiste,
                        'prestations': prestations,
                        'error_message': 'Une erreur est survenue lors de la création de la prestation.'
                    })

        # Préparer les données pour le formulaire
        prestations = CentreSantePrestation.objects.filter(
            centre_sante=request.user.centre_sante,
            prestation__categorie="hospitalisation"
        )
        medecins = MedecinTraitant.objects.filter(centre_sante=request.user.centre_sante)

        return render(request, 'frontoffice/priseencharge/ajouter_prestationshospi.html', {
            'mutualiste': mutualiste,
            'prestations': prestations,
            'medecins': medecins
        })

    else:
        # Si aucune prise en charge valide, proposer d'en créer une nouvelle
        if request.method == "POST":
            # Debugging pour afficher les données du formulaire
            print(request.POST)

            prestation_id = request.POST.get('prestation')
            medecin_id = request.POST.get('medecin')
            description_clinique = request.POST.get('description_clinique')

            if prestation_id and medecin_id:
                try:
                    # Récupération de la prestation et du médecin
                    prestation = get_object_or_404(CentreSantePrestation, prestation=prestation_id, centre_sante=request.user.centre_sante)
                    medecin = get_object_or_404(MedecinTraitant, id=medecin_id)

                    # Création d'une nouvelle prise en charge
                    prise_en_charge = PriseEnCharge.objects.create(
                        mutualiste=mutualiste,
                        centre=request.user.centre_sante,
                        date_prise_en_charge=date.today(),
                        duree_validite=0
                    )

                    # Calculer les montants
                    montant_total = calculer_montant_total(mutualiste, prestation)
                    montant_pris_en_charge = calculer_montant_pris_en_charge(mutualiste, prestation)

                    # Création de la prestation
                    Prestation.objects.create(
                        prise_en_charge=prise_en_charge,
                        centre_sante=request.user.centre_sante,
                        prestation=prestation.prestation,
                        medecin_traitant=medecin,
                        montant_total=montant_total,
                        montant_pris_en_charge=montant_pris_en_charge,
                        montant_moderateur=montant_total - montant_pris_en_charge,
                        tiers_payant=True,
                        description=description_clinique,
                        statut_validation=True,
                        date_validation=date.today()
                    )

                    return redirect('detail_prise_en_charge', prise_en_charge_id=prise_en_charge.id)

                except Exception as e:
                    # Si une erreur se produit, renvoyer un message d'erreur
                    print(f"Erreur lors de la création de la prise en charge: {e}")
                    return render(request, 'frontoffice/priseencharge/ajouter_prestations.html', {
                        'mutualiste': mutualiste,
                        'prestations': prestations,
                        'medecins': medecins,
                        'error_message': 'Une erreur est survenue lors de la création de la prise en charge.'
                    })

        prestations = CentreSantePrestation.objects.filter(
            centre_sante=request.user.centre_sante,
            prestation__categorie="consultation"
        )
        medecins = MedecinTraitant.objects.filter(centre_sante=request.user.centre_sante)

        return render(request, 'frontoffice/priseencharge/ajouter_prestations.html', {
            'mutualiste': mutualiste,
            'prestations': prestations,
            'medecins': medecins
        })
        
def ajouter_prestationshospibeneficiaire(request: HttpRequest, id: int):
    mutualiste = get_object_or_404(Beneficiaire, id=id)

    # Récupérer la dernière prise en charge du mutualiste
    last_prise_en_charge = PriseEnCharge.objects.filter(beneficiaire=mutualiste).order_by('-date_prise_en_charge').first()

    prestations = []  # Initialisation de la variable prestations

    if last_prise_en_charge and last_prise_en_charge.duree_validite > 0:
        if request.method == "POST":
            # Debugging pour afficher les données du formulaire
            print(request.POST)
            print(f"Centre santé utilisateur: {request.user.centre_sante}")

            prestation_id = request.POST.get('prestation')
            medecin_id = request.POST.get('medecin')
            motif_hospitalisation = request.POST.get('motif_hospitalisation')
            date_sortie_str = request.POST.get('date_sortie')
            duree_validite = int(request.POST.get('duree_validite', 0))  # Convertir en int
            fichier_hospitalisation = request.FILES.get('fichier_hospitalisation')  # Récupérer le fichier

            if prestation_id and medecin_id:
                try:
                    # Récupération de la prestation et du médecin
                    prestation = get_object_or_404(CentreSantePrestation, prestation=prestation_id, centre_sante=request.user.centre_sante)
                    medecin = get_object_or_404(MedecinTraitant, id=medecin_id)

                    # Calculer le montant pris en charge
                    montant_pris_en_charge = calculer_montant_pris_en_charge(mutualiste.mutualiste, prestation)

                    # Calculer la date de sortie
                    date_sortie = date.today() + timedelta(days=duree_validite)

                    # Vérifier s'il existe déjà une hospitalisation pour cette prise en charge
                    hospitalisation_existante = Hospitalisation.objects.filter(
                        prise_en_charge=last_prise_en_charge
                    ).exclude(statut_prise_en_charge=Hospitalisation.StatutPriseEnCharge.REFUSÉE).exists()

                    if hospitalisation_existante:
                        return render(request, 'frontoffice/priseencharge/ajouter_prestationshospi.html', {
                            'mutualiste': mutualiste,
                            'prestations': prestations,
                            'medecins': medecins,
                            'error_message': 'Une hospitalisation existe déjà pour cette prise en charge.'
                        })
                        
                    # Création de l'hospitalisation
                    hospi = Hospitalisation.objects.create(
                        prise_en_charge=last_prise_en_charge,
                        mutualiste=mutualiste.mutualiste,
                        beneficiaire=mutualiste,
                        centre_sante=request.user.centre_sante,
                        date_sortie=date_sortie,
                        motif_hospitalisation=motif_hospitalisation,
                        fichier_hospitalisation=fichier_hospitalisation,
                        statut_prise_en_charge=Hospitalisation.StatutPriseEnCharge.EN_ATTENTE,
                        montant_prise_en_charge=montant_pris_en_charge,
                        duree_validite=duree_validite
                    )

                    # Calculer le montant total et le montant pris en charge
                    montant_total = calculer_montant_total(mutualiste.mutualiste, prestation)

                    # Création de la prestation
                    prestation_obj = Prestation.objects.create(
                        prise_en_charge=last_prise_en_charge,
                        centre_sante=request.user.centre_sante,
                        prestation=prestation.prestation,
                        medecin_traitant=medecin,
                        montant_total=montant_total,
                        montant_pris_en_charge=montant_pris_en_charge,
                        montant_moderateur=montant_total - montant_pris_en_charge,
                        tiers_payant=True,
                        description=motif_hospitalisation,
                        statut_validation=False,
                        date_validation=date.today()
                    )
                    
                    # Ajout de la prestation à l'hospitalisation
                    hospi.prestations.add(prestation_obj)
                    messages.success(request, "La demande d'hospitalisation a été ajoutée avec succès !")

                    return redirect('detail_prise_en_charge', prise_en_charge_id=last_prise_en_charge.id)

                except Exception as e:
                    # Si une erreur se produit, renvoyer un message d'erreur
                    print(f"Erreur lors de la création de la prestation: {e}")
                    return render(request, 'frontoffice/priseencharge/ajouter_prestationshospi.html', {
                        'mutualiste': mutualiste,
                        'prestations': prestations,
                        'error_message': 'Une erreur est survenue lors de la création de la prestation.'
                    })

        # Préparer les données pour le formulaire
        prestations = CentreSantePrestation.objects.filter(
            centre_sante=request.user.centre_sante,
            prestation__categorie="hospitalisation"
        )
        medecins = MedecinTraitant.objects.filter(centre_sante=request.user.centre_sante)

        return render(request, 'frontoffice/priseencharge/ajouter_prestationshospi.html', {
            'mutualiste': mutualiste,
            'prestations': prestations,
            'medecins': medecins
        })

    else:
        # Si aucune prise en charge valide, proposer d'en créer une nouvelle
        if request.method == "POST":
            # Debugging pour afficher les données du formulaire
            print(request.POST)

            prestation_id = request.POST.get('prestation')
            medecin_id = request.POST.get('medecin')
            description_clinique = request.POST.get('description_clinique')

            if prestation_id and medecin_id:
                try:
                    # Récupération de la prestation et du médecin
                    prestation = get_object_or_404(CentreSantePrestation, prestation=prestation_id, centre_sante=request.user.centre_sante)
                    medecin = get_object_or_404(MedecinTraitant, id=medecin_id)

                    # Création d'une nouvelle prise en charge
                    prise_en_charge = PriseEnCharge.objects.create(
                        mutualiste=mutualiste.mutualiste,
                        beneficiaire=mutualiste,
                        centre=request.user.centre_sante,
                        date_prise_en_charge=date.today(),
                        duree_validite=0
                    )

                    # Calculer les montants
                    montant_total = calculer_montant_total(mutualiste, prestation)
                    montant_pris_en_charge = calculer_montant_pris_en_charge(mutualiste, prestation)

                    # Création de la prestation
                    Prestation.objects.create(
                        prise_en_charge=prise_en_charge,
                        centre_sante=request.user.centre_sante,
                        prestation=prestation.prestation,
                        medecin_traitant=medecin,
                        montant_total=montant_total,
                        montant_pris_en_charge=montant_pris_en_charge,
                        montant_moderateur=montant_total - montant_pris_en_charge,
                        tiers_payant=True,
                        description=description_clinique,
                        statut_validation=True,
                        date_validation=date.today()
                    )

                    return redirect('detail_prise_en_charge', prise_en_charge_id=prise_en_charge.id)

                except Exception as e:
                    # Si une erreur se produit, renvoyer un message d'erreur
                    print(f"Erreur lors de la création de la prise en charge: {e}")
                    return render(request, 'frontoffice/priseencharge/ajouter_prestations.html', {
                        'mutualiste': mutualiste,
                        'prestations': prestations,
                        'medecins': medecins,
                        'error_message': 'Une erreur est survenue lors de la création de la prise en charge.'
                    })

        prestations = CentreSantePrestation.objects.filter(
            centre_sante=request.user.centre_sante,
            prestation__categorie="consultation"
        )
        medecins = MedecinTraitant.objects.filter(centre_sante=request.user.centre_sante)

        return render(request, 'frontoffice/priseencharge/ajouter_prestations.html', {
            'mutualiste': mutualiste,
            'prestations': prestations,
            'medecins': medecins
        })
        
# ============================================================ VALIDATIONS DES EXAMENS ET HOSPITALISATIONS =============================================================
def liste_validations(request):
    hospitalisations = Hospitalisation.objects.filter(statut_prise_en_charge=Hospitalisation.StatutPriseEnCharge.EN_ATTENTE)
    examens = ExamenMedical.objects.filter(statut=ExamenMedical.StatutExamen.EN_ATTENTE)
    optiques = PrestationLunetterie.objects.filter(statut=PrestationLunetterie.StatutOptique.EN_ATTENTE)
    
    return render(request, 'frontoffice/priseencharge/validations/liste_validations.html', {'hospitalisations': hospitalisations, 'examens': examens,'optiques':optiques})

def valider_hospitalisationB(request, id):
    hospitalisation = get_object_or_404(Hospitalisation, id=id)
    
    # Récupérer les 5 dernières hospitalisations du mutualiste, excluant l'actuelle
    hospitalisations_precedentes = Hospitalisation.objects.filter(
        mutualiste=hospitalisation.mutualiste
    ).exclude(id=hospitalisation.id).order_by('-date_admission')[:5]
    
    if request.method == "POST":
        form = HospitalisationValidationForm(request.POST, instance=hospitalisation)
        if form.is_valid():
            form.save()
            
            # Vérifier si le statut a été mis à "Validée"
            if form.statut_prise_en_charge == form.StatutPriseEnCharge.VALIDÉE:
                # Mettre à jour les prestations associées à cette hospitalisation
                prestations_associees = Prestation.objects.filter(id=hospitalisation.prestations)
                prestations_associees.update(statut_validation=True)  # Validation des prestations

            
            return redirect('liste_validations')
    else: 
        form = HospitalisationValidationForm(instance=hospitalisation)
    
    return render(request, 'frontoffice/priseencharge/validations/valider_hospitalisation.html', {'form': form, 'hospitalisation': hospitalisation ,
            'hospitalisations_precedentes': hospitalisations_precedentes})




def valider_hospitalisation(request, id):
    hospitalisation = get_object_or_404(Hospitalisation, id=id)

    # Récupérer les 5 dernières hospitalisations du mutualiste, excluant l'actuelle
    hospitalisations_precedentes = Hospitalisation.objects.filter(
        mutualiste=hospitalisation.mutualiste
    ).exclude(id=hospitalisation.id).order_by('-date_admission')[:5]

    if request.method == "POST":
        form = HospitalisationValidationForm(request.POST, instance=hospitalisation)
        if form.is_valid():
            hospitalisation = form.save()  # Enregistre les modifications

            # Vérifier si le statut a été mis à "Validée"
            if hospitalisation.statut_prise_en_charge == Hospitalisation.StatutPriseEnCharge.VALIDÉE:
                # Mettre à jour les prestations associées à cette hospitalisation
               # Récupérer les prestations associées à cette hospitalisation
                prestations_associees = hospitalisation.prestations.all()
                
                # Mise à jour du statut de validation
                prestations_associees.update(statut_validation=True)
                
                mois_actuel = now().month
                annee_actuelle = now().year
                dernier_jour_du_mois = calendar.monthrange(annee_actuelle, mois_actuel)[1]
                # 📌 Vérifier si une facture existe pour ce centre et ce mois, sinon la créer
                facture, created = Facture.objects.get_or_create(
                    centre=hospitalisation.centre_sante,
                    numero_facture=f"{mois_actuel:02}{annee_actuelle}",  # 🔹 Clé unique pour le mois
                    defaults={  # 🔹 Valeurs si la facture est créée
                        'total_mutualiste': 0,
                        'total_mutuelle': 0,
                        'total_general': 0,
                        'date_debut': f"{annee_actuelle}-{mois_actuel:02}-01",
                        'date_fin': f"{annee_actuelle}-{mois_actuel:02}-{dernier_jour_du_mois}"
                    }
                )
                # 📝 Calcul des montants totaux
                total_montant_moderateur = prestations_associees.aggregate(Sum('montant_moderateur'))['montant_moderateur__sum'] or 0
                total_montant_pris_en_charge = prestations_associees.aggregate(Sum('montant_pris_en_charge'))['montant_pris_en_charge__sum'] or 0
                
                
                # 📝 Mettre à jour les montants de la facture
                facture.total_mutualiste += total_montant_moderateur
                facture.total_mutuelle += total_montant_pris_en_charge
                facture.total_general = facture.total_mutualiste + facture.total_mutuelle
                facture.save()

                # 📝 Mettre à jour les montants de la facture
                #facture.total_mutualiste += prestations_associees.montant_moderateur
                #facture.total_mutuelle += prestations_associees.montant_pris_en_charge
                #facture.total_general = facture.total_mutualiste + facture.total_mutuelle
                #facture.save()

            messages.success(request, "L'hospitalisation a été validée avec succès.")
            return redirect('liste_validations')

    else:
        form = HospitalisationValidationForm(instance=hospitalisation)

    return render(request, 'frontoffice/priseencharge/validations/valider_hospitalisation.html', {
        'form': form,
        'hospitalisation': hospitalisation,
        'hospitalisations_precedentes': hospitalisations_precedentes
    })


def valider_examen(request, id):
    examen = get_object_or_404(ExamenMedical, id=id)
    
    # Récupérer les 5 derniers examens du mutualiste (excluant l'actuel)
    examens_precedents = ExamenMedical.objects.filter(
        mutualiste=examen.mutualiste
    ).exclude(id=examen.id).order_by('-date_prescription')[:5]
    
    if request.method == "POST":
        form = ExamenValidationForm(request.POST, instance=examen)
        if form.is_valid():
            # Mettre à jour la date de réalisation et enregistrer l'examen
            examen.date_realisation = date.today()
            form.save()

            # Vérifier si l'examen est validé
            if examen.statut == 'validee':
                # Calcul des montants en fonction de la prestation
                examenprice = get_object_or_404(CentreSantePrestation, prestation=examen.type_examen.id,centre_sante=examen.centre_sante.id)
                print(examenprice)
                montant_total = calculer_montant_total(examen.mutualiste, examenprice)
                montant_pris_en_charge = calculer_montant_pris_en_charge(examen.mutualiste, examenprice)
                montant_moderateur = montant_total - montant_pris_en_charge  

                # Création de la prestation avec validation automatique
                Prestation.objects.create(
                    prise_en_charge=examen.prise_en_charge, 
                    centre_sante=examen.centre_sante,
                    prestation=examen.type_examen,  # Correction ici
                    medecin_traitant=examen.prise_en_charge.medecin_traitant,  # Supposant qu'il y a un médecin traitant
                    montant_total=montant_total,
                    montant_pris_en_charge=montant_pris_en_charge,
                    montant_moderateur=montant_moderateur,
                    tiers_payant=True,
                    description=examen.resultat_texte,
                    statut_validation=True,
                    date_validation=now().date() 
                )
                
                # Gestion de la facture du mois
                mois_actuel = now().month
                annee_actuelle = now().year
                dernier_jour_du_mois = calendar.monthrange(annee_actuelle, mois_actuel)[1]
                facture, created = Facture.objects.get_or_create(
                    centre=examen.centre_sante,
                    numero_facture=f"{mois_actuel:02}{annee_actuelle}",  # 🔹 Clé unique pour le mois
                    defaults={
                        'total_mutualiste': 0,
                        'total_mutuelle': 0,
                        'total_general': 0,
                        'date_debut': f"{annee_actuelle}-{mois_actuel:02}-01",
                        'date_fin': f"{annee_actuelle}-{mois_actuel:02}-{dernier_jour_du_mois}"
                    }
                )

                # Mise à jour des montants de la facture
                facture.total_mutualiste += montant_moderateur
                facture.total_mutuelle += montant_pris_en_charge
                facture.total_general = facture.total_mutualiste + facture.total_mutuelle
                facture.save()
                
            return redirect('liste_validations')

    else:
        form = ExamenValidationForm(instance=examen)
    
    return render(
        request, 
        'frontoffice/priseencharge/validations/valider_examen.html',
        {'form': form, 'examen': examen, 'examens_precedents': examens_precedents}
    )

def valider_optique(request, id):
    examen = get_object_or_404(PrestationLunetterie, id=id)
    nature = get_object_or_404(NaturePriseEnCharge, nature='Optique')
    
    # Récupérer les 5 derniers examens du mutualiste (excluant l'actuel)
    examens_precedents = PrestationLunetterie.objects.filter(
        mutualiste=examen.mutualiste
    ).exclude(id=examen.id).order_by('-date_prestation')[:5]
    
    if request.method == "POST":
        form = OptiqueValidationForm(request.POST, instance=examen)
        if form.is_valid():
            # Mettre à jour la date de réalisation et enregistrer l'examen
            examen.date_prestation = date.today()
            form.save()

            # Vérifier si l'examen est validé
            if examen.statut == 'validee':
                # Calcul des montants en fonction de la prestation
                examenprice = get_object_or_404(CentreSantePrestation, prestation=examen.prestation.id,centre_sante=examen.centre_sante.id)
                print(examenprice)
                montant_total = examenprice.tarif_personnalise
                montant_pris_en_charge = examenprice.tarif_personnalise
                montant_moderateur = examenprice.tarif_personnalise
                
                duree_validite = calculer_duree_validiteoptique(examen.mutualiste)  # Calcul de la durée de validité
                # Création d'une nouvelle prise en charge
                prise_en_charge = PriseEnCharge.objects.create(
                    medecin_traitant=examen.medecin_traitant,
                    nature=nature,
                    mutualiste=examen.mutualiste,
                    centre=examen.centre_sante,
                    date_prise_en_charge=date.today(),
                    duree_validite=duree_validite
                )

                # Création de la prestation avec validation automatique
                Prestation.objects.create(
                    prise_en_charge=prise_en_charge,
                    centre_sante=examen.centre_sante,
                    prestation=examen.prestation,  # Correction ici
                    medecin_traitant=examen.medecin_traitant,  # Supposant qu'il y a un médecin traitant
                    montant_total=montant_total,
                    montant_pris_en_charge=montant_pris_en_charge,
                    montant_moderateur=montant_moderateur,
                    tiers_payant=True,
                    description=examen.description,
                    statut_validation=True,
                    date_validation=now().date()
                )
                
                
                
                # Gestion de la facture du mois
                mois_actuel = now().month
                annee_actuelle = now().year
                dernier_jour_du_mois = calendar.monthrange(annee_actuelle, mois_actuel)[1]
                facture, created = Facture.objects.get_or_create(
                    centre=examen.centre_sante,
                    numero_facture=f"{mois_actuel:02}{annee_actuelle}",  # 🔹 Clé unique pour le mois
                    defaults={
                        'total_mutualiste': 0,
                        'total_mutuelle': 0,
                        'total_general': 0,
                        'date_debut': f"{annee_actuelle}-{mois_actuel:02}-01",
                        'date_fin': f"{annee_actuelle}-{mois_actuel:02}-{dernier_jour_du_mois}"
                    }
                )

                # Mise à jour des montants de la facture
                facture.total_mutualiste += montant_moderateur
                facture.total_mutuelle += montant_pris_en_charge
                facture.total_general = facture.total_mutualiste + facture.total_mutuelle
                facture.save()
                
            # Mise à jour de l'examen avec la prise en charge
                examen.prise_en_charge = prise_en_charge
                examen.save()
            
            return redirect('liste_validations')

    else:
        form = OptiqueValidationForm(instance=examen)
    
    return render(
        request, 
        'frontoffice/priseencharge/validations/valider_examen.html',
        {'form': form, 'examen': examen, 'examens_precedents': examens_precedents}
    )

# ============================================================ PRESCRIPTION MEDICAMENTS =============================================================
def ajouter_prescription(request, id):
    prise_en_charge = get_object_or_404(PriseEnCharge, id=id)

    if request.method == "POST":
        prescription_form = PrescriptionForm(request.POST)
        formset = MedicamentPrescrisFormSet(request.POST)

        if prescription_form.is_valid() and formset.is_valid():
            prescription = prescription_form.save(commit=False)
            prescription.prise_en_charge = prise_en_charge
            prescription.save()  # Enregistre la prescription

            medicaments = formset.save(commit=False)
            for medicament in medicaments:
                medicament.prestation_prescription = prescription  # Associer les médicaments à la prescription
                medicament.save()

            return redirect('detail_prise_en_charge', prise_en_charge_id=prise_en_charge.id)
        else:
            print("📌 Erreurs du formulaire Prescription:", prescription_form.errors)
            print("📌 Erreurs du Formset:", formset.errors)

    else:
        prescription_form = PrescriptionForm(initial={'prise_en_charge': id})
        formset = MedicamentPrescrisFormSet()

    return render(request, 'frontoffice/priseencharge/ajouter_prescription.html', {
        'prescription_form': prescription_form,
        'formset': formset,'prise_en_charge':prise_en_charge,
    })


def prescription_update(request, pk):
    prescription = get_object_or_404(Prescription, pk=pk)
    if request.method == "POST":
        prescription_form = PrescriptionForm(request.POST, instance=prescription)
        formset = MedicamentPrescrisFormSet(request.POST, instance=prescription)

        if prescription_form.is_valid() and formset.is_valid():
            prescription_form.save()
            formset.save()
            return redirect('prescription_list')

    else:
        prescription_form = PrescriptionForm(instance=prescription)
        formset = MedicamentPrescrisFormSet(instance=prescription)

    return render(request, 'prescription_form.html', {
        'prescription_form': prescription_form,
        'formset': formset,
    })

# ============================================================ MEDICAMENTS =============================================================
# 📌 Liste des médicaments
def liste_medicaments(request):
    medicaments = Medicament.objects.all()
    return render(request, 'backoffice/medicaments/medoc_liste.html', {'medicaments': medicaments})

# 📌 Ajouter un médicament
def ajouter_medicament(request):
    if request.method == "POST":
        form = MedicamentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Médicament ajouté avec succès !")
            return redirect('liste_medicament')
    else:
        form = MedicamentForm()
    return render(request, 'backoffice/medicaments/medoc_formulaire.html', {'form': form})

# 📌 Modifier un médicament
def modifier_medicament(request, pk):
    medicament = get_object_or_404(Medicament, pk=pk)
    if request.method == "POST":
        form = MedicamentForm(request.POST, instance=medicament)
        if form.is_valid():
            form.save()
            messages.success(request, "Médicament modifié avec succès !")
            return redirect('liste_medicament')
    else:
        form = MedicamentForm(instance=medicament)
    return render(request, 'backoffice/medicaments/medoc_formulaire.html', {'form': form})

# 📌 Supprimer un médicament
def supprimer_medicament(request, pk):
    medicament = get_object_or_404(Medicament, pk=pk)
    medicament.delete()
    messages.success(request, "Médicament supprimé avec succès !")
    return redirect('liste_medicament')

# 📌 Importation de médicaments depuis Excel
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Medicament, Regime

def importer_medicaments(request):
    if request.method == 'POST':
        fichier_excel = request.FILES.get('fichier_excel')
        
        if not fichier_excel:
            messages.error(request, "Veuillez sélectionner un fichier Excel.")
            return redirect('importer_medicaments')
        
        try:
            # Lire le fichier Excel avec pandas
            df = pd.read_excel(fichier_excel)

            # Vérifier que le fichier contient les colonnes nécessaires
            colonnes_requises = ['code', 'nom', 'description', 'dci', 'molecule', 'typem', 'regime', 'disponible_en_pharmacie', 'cout_unitaire']
            if not all(colonne in df.columns for colonne in colonnes_requises):
                messages.error(request, "Le fichier Excel doit contenir les colonnes suivantes : " + ", ".join(colonnes_requises))
                return redirect('importer_medicaments')

            # Parcourir les lignes et créer des objets `Medicament`
            for _, row in df.iterrows():
                # Vérifier si le régime d'assurance existe
                regime = None
                if pd.notna(row['regime']):  # Vérifie si la valeur n'est pas NaN
                    try:
                        regime = Regime.objects.get(id=row['regime'])
                    except Regime.DoesNotExist:
                        messages.warning(request, f"Le régime ID '{row['regime']}' n'existe pas.")
                        continue  # Passer à la ligne suivante

                # Créer ou mettre à jour l'objet Medicament
                Medicament.objects.update_or_create(
                    code=row['code'],  # Identification unique
                    defaults={
                        'nom': row['nom'],
                        'description': row['description'],
                        'dci': row['dci'],
                        'molecule': row['molecule'],
                        'typem': row['typem'],
                        'regime': regime,
                        'disponible_en_pharmacie': bool(row['disponible_en_pharmacie']),
                        'cout_unitaire': row['cout_unitaire']
                    }
                )
            
            messages.success(request, "Les médicaments ont été importés avec succès !")
            return redirect('liste_medicament')

        except Exception as e:
            messages.error(request, f"Erreur lors de l'importation du fichier : {e}")
            return redirect('importer_medicaments')

    return render(request, 'backoffice/medicaments/importer_medicaments.html')



def valider_code_prescription(request):
    code_prescription = request.GET.get("code_prescription")
    # On filtre les prescriptions en attente par code_prescription
    prescription = Prescription.objects.filter(code_prescription=code_prescription, statut=Prescription.StatutPrescription.EN_ATTENTE).first()

    if prescription:
        # On récupère les médicaments prescrits avec les détails requis
        medicaments = [
            {
                "id": medicament.medicament.id,
                "nom": medicament.medicament.nom,
                "prix": medicament.medicament.cout_unitaire  # Si prix est un attribut de 'Medicament'
            }
            for medicament in prescription.medicaments_prescris.all()
        ]
        
        return JsonResponse({
            "status": "success",
            "data": {
                "id": prescription.id,
                "mutualiste": prescription.prise_en_charge.mutualiste.id,
                "medicaments": medicaments
            }
        })
    else:
        return JsonResponse({"status": "error", "message": "Prescription non trouvée ou déjà traitée."})


# ============================================================ DISPENSATION PHARMACIE ==============================================
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import PrestationPharmacie, MedicamentUtilise, Prescription, Medicament
import json


    
def calculer_montant_pris_en_chargeprescription(mutualiste, total_medicaments):
    """
    Calculer le montant pris en charge par la mutuelle en fonction du total des médicaments.
    """
    # Vérifier que le montant total des médicaments est bien défini
    if total_medicaments is None or total_medicaments <= 0:
        raise ValueError("Le montant total des médicaments doit être un nombre positif.")

    # Vérifier que le taux de couverture est valide
    taux_couverture = mutualiste.regime.taux_couverture if mutualiste.regime.taux_couverture is not None else 0
    if taux_couverture == 0:
        raise ValueError("Le taux de couverture de la mutuelle est invalide ou manquant.")
    
    # Calcul du montant pris en charge
    montant_pris_en_charge = total_medicaments * (taux_couverture / 100)  # Conversion en pourcentage

    # Appliquer le plafond annuel de couverture si défini
    plafond_annuel = mutualiste.regime.plafond_annuel_couverture if mutualiste.regime.plafond_annuel_couverture else None
    if plafond_annuel:
        montant_pris_en_charge = min(montant_pris_en_charge, plafond_annuel)

    return montant_pris_en_charge

@csrf_protect
def ajouter_dispensation(request, id: int):
    prescription = get_object_or_404(Prescription, id=id)
    medicament_list = Medicament.objects.all()

    if request.method == "POST":
        try:
            mutualiste_id = request.POST.get("mutualiste_id")

            if not mutualiste_id:
                return JsonResponse({"status": "error", "message": "Le mutualiste est requis."})

            # Création de la prestation pharmacie
            prestation = PrestationPharmacie.objects.create(
                prescription=prescription,
                mutualiste_id=mutualiste_id,
                centre_sante=request.user.centre_sante,
            )

            total_medicaments = Decimal("0.00")
            total_mutuelle = Decimal("0.00")
            total_mutualiste = Decimal("0.00")

            for key, value in request.POST.items():
                if key.startswith("quantite_"):
                    try:
                        med_id = key.split("_")[1]
                        medicament = Medicament.objects.get(id=med_id)
                        quantite = int(value)

                        if quantite <= 0:
                            return JsonResponse({"status": "error", "message": f"Quantité invalide pour {medicament.nom}."})

                        prix_key = f"prix_{med_id}"
                        cout_unitaire = Decimal(request.POST.get(prix_key, medicament.cout_unitaire))

                        # Enregistrement du médicament utilisé
                        MedicamentUtilise.objects.create(
                            prestation_pharmacie=prestation,
                            medicament=medicament,
                            quantite_servie=quantite,
                            cout_unitaire=cout_unitaire
                        )

                        # Calcul du montant total pour ce médicament
                        montant_total_med = quantite * cout_unitaire
                        total_medicaments += montant_total_med

                        # Récupération du mutualiste associé à la prescription
                        mutualiste = prescription.prise_en_charge.mutualiste

                        # Calcul du montant pris en charge et du montant à la charge du mutualiste
                        montant_pris_en_charge = calculer_montant_pris_en_chargeprescription(mutualiste, total_medicaments)
                        montant_moderateur = total_medicaments - montant_pris_en_charge


                        total_mutuelle += montant_pris_en_charge
                        total_mutualiste += montant_moderateur
                    
                    except Medicament.DoesNotExist:
                        return JsonResponse({"status": "error", "message": f"Médicament ID {med_id} introuvable."})
                    except ValueError:
                        return JsonResponse({"status": "error", "message": f"Valeur incorrecte pour {med_id}."})

            # Gestion de la facture mensuelle
            mois_actuel = now().month
            annee_actuelle = now().year
            facture, created = Facture.objects.get_or_create(
                centre=request.user.centre_sante,
                defaults={
                    'total_mutualiste': Decimal("0.00"),
                    'total_mutuelle': Decimal("0.00"),
                    'total_general': Decimal("0.00")
                }
            )

            # Mise à jour des montants de la facture
            facture.total_mutualiste += total_mutualiste
            facture.total_mutuelle += total_mutuelle
            facture.total_general = facture.total_mutualiste + facture.total_mutuelle
            facture.save()

            # Mise à jour du montant total et du statut de la prescription
            prestation.calculer_montant_total()
            prescription.statut = "validée"
            prescription.save()

            return redirect('tableau_de_bord_pharmacie')

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    # Récupération des médicaments liés à la prescription
    medicaments = [
        {
            "id": mp.medicament.id,
            "nom": mp.medicament.nom,
            "prix": mp.medicament.cout_unitaire,
            "quantite": mp.quantite_prescrite
        }
        for mp in prescription.medicaments_prescris.all()
    ]

    return render(request, 'frontoffice/priseencharge/ajouter_dispensation_formulaire.html', {
        'prescription_id': id,
        'medicaments': medicaments,
        'prescription': prescription,
        'medicament_list': medicament_list
    })




def generer_pdf_dispensation(prescription, prestation, medicaments):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Entête
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, height - 50, "Dispensation de Médicaments")
    
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 80, f"Mutualiste: {prestation.mutualiste_id}")
    p.drawString(50, height - 100, f"Centre de Santé: {prestation.centre_sante.nom}")
    p.drawString(50, height - 120, f"Date: {prestation.date_prestation}")

    # Tableau des médicaments
    y_position = height - 160
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y_position, "Nom Médicament")
    p.drawString(250, y_position, "Quantité")
    p.drawString(350, y_position, "Prix Unitaire")
    p.drawString(450, y_position, "Total")
    
    y_position -= 20
    p.setFont("Helvetica", 12)

    for medicament in medicaments:
        p.drawString(50, y_position, medicament["nom"])
        p.drawString(250, y_position, str(medicament["quantite"]))
        p.drawString(350, y_position, f"{medicament['prix_unitaire']:.2f} FCFA")
        p.drawString(450, y_position, f"{medicament['total']:.2f} FCFA")
        y_position -= 20

    # Total général
    p.setFont("Helvetica-Bold", 12)
    p.drawString(350, y_position - 20, "Total:")
    p.drawString(450, y_position - 20, f"{sum(m['total'] for m in medicaments):.2f} FCFA")

    # Générer le PDF
    p.showPage()
    p.save()
    buffer.seek(0)

    # Retourner le fichier en réponse HTTP
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="dispensation_{prestation.id}.pdf"'
    return response

# ============================================================ LISTE DETAIL DES PRISES EN CHARGE PAR CENTRE ============================================== 
@login_required
def listedetail_prestations(request):
    centre_sante = request.user.centre_sante  # Centre de santé connecté
    prestations = (Prestation.objects.filter(centre_sante=centre_sante)
        .select_related("prise_en_charge")
        .order_by("date_prestation", "prise_en_charge__date_creation")  
    )

    
    #now = timezone.now()
    #annee_courante = now.year
    #mois_courant = str(now.month).zfill(2)
    now = timezone.now()
    annee_courante = now.year
    mois_courant = now.month
    
    print("Date actuelle:", now)
    print("Année courante:", annee_courante)
    print("Mois courant:", mois_courant)  # Affichera '02' au lieu de '2'
    
    # Statistiques globales
    total_prises_en_charge = PriseEnCharge.objects.filter(centre=centre_sante,date_creation__year=annee_courante).count()

    # Prestations validées pour le mois en cours
    total_prestationsvalide = Prestation.objects.filter(
        centre_sante=centre_sante, 
        statut_validation=True, 
        #date_prestation__date__year=annee_courante,  # Ajout de `__date`
        #date_prestation__date__month=mois_courant
    ).count()
    print("total prestationsvalide:", total_prestationsvalide)

    # Prestations non validées
    total_prestationsnonvalide = Prestation.objects.filter(
        centre_sante=centre_sante, 
        statut_validation=False
    ).count()

    # Total des prestations
    total_prestations = Prestation.objects.filter(centre_sante=centre_sante).count()

    # Montant total des prestations validées pour le mois en cours
    montant_total_prestations = Prestation.objects.filter(
        centre_sante=centre_sante, 
        statut_validation=True, 
        #date_prestation__year=annee_courante, 
        #date_prestation__month=mois_courant
    ).aggregate(Sum('montant_total'))['montant_total__sum'] or 0


    for prestation in prestations:
        # Vérifier si la prestation est validée
        if not prestation.statut_validation:
            prestation.statut_validation_html = mark_safe('<span style="color: red; font-weight: bold;">Non validée</span>')
        else:
            prestation.statut_validation_html = mark_safe('<span style="color: green; font-weight: bold;">Validée</span>')

    return render(request, "frontoffice/priseencharge/listedetail_prestations.html", {"prestations": prestations,
                                                                                      'total_prises_en_charge':total_prises_en_charge,
                                                                                      'total_prestationsvalide': total_prestationsvalide,
                                                                                      'total_prestationsnonvalide': total_prestationsnonvalide,
                                                                                      'total_prestations' : total_prestations,
                                                                                      'montant_total_prestations' : montant_total_prestations
                                                                                      })
    
# ============================================================ LISTE DETAIL DES PRISES EN CHARGE PAR PHARMACIE ============================================== 
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q, Case, When, Value, CharField
from django.utils.safestring import mark_safe
from django.shortcuts import render
from datetime import datetime

@login_required
def listedetail_prestationspharma(request):
    centre_sante = request.user.centre_sante  # Centre de santé connecté
    now = timezone.now()
    annee_courante = now.year
    mois_courant = str(now.month).zfill(2)  # Format '02' au lieu de '2'

    # Récupération des prestations en pharmacie
    prestations = (
        PrestationPharmacie.objects.filter(centre_sante=centre_sante)
        .select_related("prescription", "mutualiste", "centre_sante")
        .prefetch_related("medicaments_utilises")
        .annotate(
            statut_validation_html=Case(
                When(montant_total__isnull=False, then=Value(mark_safe('<span style="color: green; font-weight: bold;">Validée</span>'))),
                default=Value(mark_safe('<span style="color: red; font-weight: bold;">Non validée</span>')),
                output_field=CharField(),
            )
        )
        .order_by("-date_prestation")  # Trier par date récente
    )

    # Statistiques globales
    stats = PrestationPharmacie.objects.filter(centre_sante=centre_sante).aggregate(
        total_prises_en_charge=Count("id"),
        total_prestationsvalide=Count("id", filter=Q(montant_total__isnull=False, date_prestation__year=annee_courante, date_prestation__month=mois_courant)),
        total_prestationsnonvalide=Count("id", filter=Q(montant_total__isnull=True)),
        total_prestations=Count("id"),
        montant_total_prestations=Sum("montant_total", filter=Q(montant_total__isnull=False, date_prestation__year=annee_courante, date_prestation__month=mois_courant), default=0)
    )

    context = {
        "prestations": prestations,
        **stats  # Ajout des statistiques au contexte
    }

    return render(request, "frontoffice/priseencharge/listedetail_prestationspharma.html", context)


    
#=========================================================  SINISTRES RAPPORT EN PDF ============================================================================  
from django.utils.timezone import now
from django.db.models import Q
from datetime import timedelta

def get_prestations_par_mois(annee, mois):
    debut_mois = now().replace(year=annee, month=mois, day=1, hour=0, minute=0, second=0)
    fin_mois = (debut_mois + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

    prestations = Prestation.objects.filter(date_prestation__range=(debut_mois, fin_mois))
    prestations_pharmacie = PrestationPharmacie.objects.filter(date_prestation__range=(debut_mois, fin_mois))

    groupe_1 = prestations.filter(prestation__categorie='hospitalisation')
    groupe_2 = prestations.filter(prestation__categorie='optique')
    groupe_3 = prestations.exclude(prestation__categorie__in=['hospitalisation', 'optique'])
    groupe_4 = prestations_pharmacie  # Toutes les prestations en pharmacie

    return {
        "hospitalisation": groupe_1,
        "optique": groupe_2,
        "autres": groupe_3,
        "pharmacie": groupe_4
    }

from django.shortcuts import render
from django.http import JsonResponse
from .models import Prestation, PrestationPharmacie

def prestations_par_all(request):
    # Récupérer toutes les prestations sans filtrage par date
    prestations = Prestation.objects.all()
    prestations_pharmacie = PrestationPharmacie.objects.all()

    # Combine toutes les prestations dans un seul tableau
    all_prestations = list(prestations.values("id", "description", "date_prestation", "montant_total", "categorie"))
    all_prestations_pharmacie = list(prestations_pharmacie.values("id", "description", "date_prestation", "montant_total"))

    # Ajouter les prestations de pharmacie aux autres prestations
    all_prestations.extend(all_prestations_pharmacie)

    data = {
        "prestations": all_prestations
    }

    return render(request, "backoffice/prestations/sinistreprestationsall.html", {"prestations": all_prestations})


from django.http import JsonResponse
from django.shortcuts import render
from datetime import datetime, timedelta
from .models import Prestation, PrestationPharmacie

def prestations_par_mois(request):
    if request.method == "GET" and "date" in request.GET:
        date_str = request.GET.get("date")  # Format attendu: YYYY-MM-DD
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        annee, mois = date_obj.year, date_obj.month

        debut_mois = date_obj.replace(day=1, hour=0, minute=0, second=0)
        fin_mois = (debut_mois + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

        prestations = Prestation.objects.filter(date_prestation__range=(debut_mois, fin_mois))
        prestations_pharmacie = PrestationPharmacie.objects.filter(date_prestation__range=(debut_mois, fin_mois))

        data = {
            "hospitalisation": list(prestations.filter(prestation__categorie='hospitalisation').values()),
            "optique": list(prestations.filter(prestation__categorie='optique').values()),
            "autres": list(prestations.exclude(prestation__categorie__in=['hospitalisation', 'optique']).values()),
            "pharmacie": list(prestations_pharmacie.values())
        }
        return JsonResponse(data, safe=False)

    return render(request, "backoffice/prestations/sinistreprestations.html")


from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
def prestations_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="prestations.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # ✅ Ajout du logo
    logo_path = "static/backoffice/img/logo/logo.png"
    elements.append(Image(logo_path, width=100, height=50))  # Assurez-vous que le chemin est correct
    elements.append(Spacer(1, 20))

    # ✅ Récupération de la date
    date_str = request.GET.get("date", "")
    if date_str:
        date_obj = timezone.make_aware(datetime.strptime(date_str, "%Y-%m-%d"))
        debut_mois = date_obj.replace(day=1, hour=0, minute=0, second=0)
        fin_mois = (debut_mois + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

        mois_annee = debut_mois.strftime("%B %Y").capitalize()
        elements.append(Paragraph(f"<b>Rapport des sinistres - {mois_annee}</b>", styles["Title"]))
        elements.append(Spacer(1, 10))
            
        prestations = Prestation.objects.filter(date_prestation__range=(debut_mois, fin_mois))
        prestations_pharmacie = PrestationPharmacie.objects.filter(date_prestation__range=(debut_mois, fin_mois))

        # ✅ Catégorisation des prestations
        categories = {
            "Hospitalisation": prestations.filter(prestation__categorie='hospitalisation'),
            "Optique": prestations.filter(prestation__categorie='optique'),
            "Ambulatoires": prestations.exclude(prestation__categorie__in=['hospitalisation', 'optique']),
            "Pharmacie": prestations_pharmacie,
        }

        for categorie, prestations_list in categories.items():
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(f"<b>{categorie}</b>", styles["Heading2"]))

            table_data = [["Centre de Santé", "Total", "Mutuelle", "Mutualiste"]]
            centres = {}

            for prestation in prestations_list:
                centre = prestation.centre_sante.nom if hasattr(prestation, 'centre_sante') and prestation.centre_sante else "Inconnu"
                if centre not in centres:
                    centres[centre] = {"total": 0, "pris_en_charge": 0, "moderateur": 0}

                centres[centre]["total"] += getattr(prestation, 'montant_total', 0)
                centres[centre]["pris_en_charge"] += getattr(prestation, 'montant_pris_en_charge', 0) or getattr(prestation, 'part_mutuelle', 0)
                centres[centre]["moderateur"] += getattr(prestation, 'montant_moderateur', 0) or getattr(prestation, 'part_mutualiste', 0)

            for centre, data in centres.items():
                table_data.append([
                centre, 
                "{:,.0f}".format(data['total']).replace(",", " "), 
                "{:,.0f}".format(data['pris_en_charge']).replace(",", " "), 
                "{:,.0f}".format(data['moderateur']).replace(",", " ")
            ])


            table = Table(table_data, colWidths=[150, 80, 80, 80])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]))

            elements.append(table)

    doc.build(elements)
    return response


# ==========================================================================================================================================================================



























# ============================================================ TEST ============================================================================================================
def valider_matricule1(request):
    matricule = request.GET.get('matricule')
    mutualiste = Mutualiste.objects.filter(code_matricule=matricule).first()
    beneficiaire = Beneficiaire.objects.filter(code_matricule=matricule).first()
    
    if mutualiste:
        return JsonResponse({
            "status": "success",
            "type": "mutualiste",
            "data": {
                'id': mutualiste.id,
                "nom": mutualiste.nom,
                "prenom": mutualiste.prenom,
                "age": mutualiste.age,
                "photo": mutualiste.photo.url if mutualiste.photo else None,
            }
        })
    elif beneficiaire:
        return JsonResponse({
            "status": "success",
            "type": "beneficiaire",
            "data": {
                'id': beneficiaire.id,
                "nom": beneficiaire.nom,
                "prenom": beneficiaire.prenom,
                "age": beneficiaire.age,
                "photo": beneficiaire.photo.url if beneficiaire.photo else None,
            }
        })
    else:
        return JsonResponse({"status": "error", "message": "Matricule non trouvé."})

def ajouter_prestations1(request, id):
    if request.method == "POST":
        mutualiste = get_object_or_404(Mutualiste, id=id)
        prestations_ids = request.POST.getlist('prestations')
        for prestation_id in prestations_ids:
            prestation = get_object_or_404(Prestation, id=prestation_id)
            PriseEnCharge.objects.create(
                mutualiste=mutualiste,
                centre=request.user.centre_sante,
                date_prise_en_charge=date.today(),
                duree_validite=prestation.duree_validite
            )
        return redirect('prise_en_charge')
    
    mutualiste = get_object_or_404(Mutualiste, id=id)
    prestations = Prestation.objects.filter(centre=request.user.centre_sante)
    return render(request, 'frontoffice/priseencharge/ajouter_prestations.html', {
        'mutualiste': mutualiste,
        'prestations': prestations,
    })

from django.http import HttpRequest

def ajouter_prestationsf(request: HttpRequest, id: int):
    mutualiste = get_object_or_404(Mutualiste, id=id)
    
    if request.method == "POST":
        prestations_ids = request.POST.getlist('prestations')
        for prestation_id in prestations_ids:
            prestation = get_object_or_404(Prestation, id=prestation_id)
            PriseEnCharge.objects.create(
                mutualiste=mutualiste,
                centre=request.user.centre_sante,
                prestation=prestation,  # Correction ici
                date_prise_en_charge=date.today(),
                duree_validite=prestation.duree_validite
            )
        return redirect('prise_en_charge')

    # Correction du filtre avec `prestation__categorie`
    prestations = CentreSantePrestation.objects.filter(
        centre_sante=request.user.centre_sante,
        prestation__categorie="consultation"
    )

    return render(request, 'frontoffice/priseencharge/ajouter_prestations.html', {
        'mutualiste': mutualiste,
        'prestations': prestations,
    })

def ajouter_prestationsddd(request, id):
    if request.method == "POST":
        mutualiste = get_object_or_404(Mutualiste, id=id)
        prestations_ids = request.POST.getlist('prestations')
        for prestation_id in prestations_ids:
            prestation = get_object_or_404(Prestation, id=prestation_id)
            PriseEnCharge.objects.create(
                mutualiste=mutualiste,
                centre=request.user.centre_sante,
                date_prise_en_charge=date.today(),
                duree_validite=prestation.duree_validite
            )
        return redirect('prise_en_charge')
    
    mutualiste = get_object_or_404(Mutualiste, id=id)
    prestations = CentreSantePrestation.objects.filter(centre_sante=request.user.centre_sante,prestation__categorie="consultation")
    return render(request, 'frontoffice/priseencharge/ajouter_prestations.html', {
        'mutualiste': mutualiste,
        'prestations': prestations,
    })

def ajouter_prestationsbon(request, id):
    if request.method == "POST":
        mutualiste = get_object_or_404(Mutualiste, id=id)
        prestations_ids = request.POST.getlist('prestations')
        for prestation_id in prestations_ids:
            prestation = get_object_or_404(Prestation, id=prestation_id)
            PriseEnCharge.objects.create(
                mutualiste=mutualiste,
                centre=request.user.centre_sante,
                date_prise_en_charge=date.today(),
                duree_validite=prestation.duree_validite
            )
        return redirect('prise_en_charge')
    
    mutualiste = get_object_or_404(Mutualiste, id=id)
    prestations = CentreSantePrestation.objects.filter(centre_sante=request.user.centre_sante)
    return render(request, 'frontoffice/priseencharge/ajouter_prestations.html', {
        'mutualiste': mutualiste,
        'prestations': prestations,
    })
    
def ajouter_prestations2(request, id):
    client = get_object_or_404(Mutualiste, id=id)
    if request.method == 'POST':
        prestation_type = request.POST.get('prestation')
        details = request.POST.get('details')
        # Ajouter la prestation
        Prestation.objects.create(client=client, type=prestation_type, details=details)
        return redirect('confirmation_page')  # Redirigez vers une page de confirmation
    return render(request, 'frontoffice/priseencharge/ajouter_prestations.html', {'client': client})

from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpRequest
from datetime import date

def ajouter_prestationsde(request: HttpRequest, id: int):
    mutualiste = get_object_or_404(Mutualiste, id=id)

    if request.method == "POST":
        print(request.POST)  # 🔍 Vérifier ce qui est envoyé dans POST
        prestation_id = request.POST.get('prestation')  # Récupère une seule prestation
        
        if prestation_id:  # Vérifie qu'une prestation a bien été sélectionnée
            prestation = get_object_or_404(Prestation, id=prestation_id)
            PriseEnCharge.objects.create(
                mutualiste=mutualiste,
                centre=request.user.centre_sante,
                prestation=prestation,  # Enregistrer la prestation
                date_prise_en_charge=date.today(),
                duree_validite=prestation.duree_validite
            )
        return redirect('prise_en_charge')

    prestations = CentreSantePrestation.objects.filter(
        centre_sante=request.user.centre_sante,
        prestation__categorie="consultation"
    )
    medecins = MedecinTraitant.objects.filter(
        centre_sante=request.user.centre_sante
    )

    return render(request, 'frontoffice/priseencharge/ajouter_prestations.html', {
        'mutualiste': mutualiste,
        'prestations': prestations,
        'medecins': medecins
    })
    
    
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpRequest, Http404
from datetime import date, timedelta

def ajouter_prestationshospii(request: HttpRequest, id: int):
    mutualiste = get_object_or_404(Mutualiste, id=id)

    # Récupérer la dernière prise en charge du mutualiste
    last_prise_en_charge = PriseEnCharge.objects.filter(mutualiste=mutualiste).order_by('-date_prise_en_charge').first()

    if last_prise_en_charge and last_prise_en_charge.duree_validite > 0:
        if request.method == "POST":
            # Debugging pour afficher les données du formulaire
            print(request.POST)

            prestation_id = request.POST.get('prestation')
            medecin_id = request.POST.get('medecin')
            motif_hospitalisation = request.POST.get('motif_hospitalisation')
            date_sortie_str = request.POST.get('date_sortie')
            duree_validite = int(request.POST.get('duree_validite', 0))  # Convertir en int
            fichier_hospitalisation = request.FILES.get('fichier_hospitalisation')  # Récupérer le fichier

            if prestation_id and medecin_id:
                try:
                    # Récupération de la prestation et du médecin
                    prestation = get_object_or_404(CentreSantePrestation, prestation=prestation_id, centre_sante=request.user.centre_sante)
                    medecin = get_object_or_404(MedecinTraitant, id=medecin_id)

                    # Calculer le montant pris en charge
                    montant_pris_en_charge = calculer_montant_pris_en_charge(mutualiste, prestation)

                    # Calculer la date de sortie
                    date_sortie = date.today() + timedelta(days=duree_validite)

                    # Création de l'hospitalisation
                    hospi = Hospitalisation.objects.create(
                        prise_en_charge=last_prise_en_charge,
                        mutualiste=mutualiste,
                        centre_sante=request.user.centre_sante,
                        date_sortie=date_sortie,
                        motif_hospitalisation=motif_hospitalisation,
                        fichier_hospitalisation=fichier_hospitalisation,
                        statut_prise_en_charge=Hospitalisation.StatutPriseEnCharge.EN_ATTENTE,
                        montant_prise_en_charge=montant_pris_en_charge,
                        duree_validite=duree_validite
                    )

                    # Calculer le montant total et le montant pris en charge
                    montant_total = calculer_montant_total(mutualiste, prestation)

                    # Création de la prestation
                    Prestation.objects.create(
                        prise_en_charge=last_prise_en_charge,
                        centre_sante=request.user.centre_sante,
                        prestation=prestation.prestation,
                        medecin_traitant=medecin,
                        montant_total=montant_total,
                        montant_pris_en_charge=montant_pris_en_charge,
                        montant_moderateur=montant_total - montant_pris_en_charge,
                        tiers_payant=True,
                        description=motif_hospitalisation,
                        statut_validation=False,
                        date_validation=date.today()
                    )

                    return redirect('detail_prise_en_charge', prise_en_charge_id=last_prise_en_charge.id)

                except Exception as e:
                    # Si une erreur se produit, renvoyer un message d'erreur
                    print(f"Erreur lors de la création de la prestation: {e}")
                    return render(request, 'frontoffice/priseencharge/ajouter_prestationshospi.html', {
                        'mutualiste': mutualiste,
                        'prestations': prestations,
                        'medecins': medecins,
                        'error_message': 'Une erreur est survenue lors de la création de la prestation.'
                    })

        # Préparer les données pour le formulaire
        prestations = CentreSantePrestation.objects.filter(
            centre_sante=request.user.centre_sante,
            prestation__categorie="hospitalisation"
        )
        medecins = MedecinTraitant.objects.filter(centre_sante=request.user.centre_sante)

        return render(request, 'frontoffice/priseencharge/ajouter_prestationshospi.html', {
            'mutualiste': mutualiste,
            'prestations': prestations,
            'medecins': medecins
        })

    else:
        # Si aucune prise en charge valide, proposer d'en créer une nouvelle
        if request.method == "POST":
            # Debugging pour afficher les données du formulaire
            print(request.POST)

            prestation_id = request.POST.get('prestation')
            medecin_id = request.POST.get('medecin')
            description_clinique = request.POST.get('description_clinique')

            if prestation_id and medecin_id:
                try:
                    # Récupération de la prestation et du médecin
                    prestation = get_object_or_404(CentreSantePrestation, prestation=prestation_id, centre_sante=request.user.centre_sante)
                    medecin = get_object_or_404(MedecinTraitant, id=medecin_id)

                    # Création d'une nouvelle prise en charge
                    prise_en_charge = PriseEnCharge.objects.create(
                        mutualiste=mutualiste,
                        centre=request.user.centre_sante,
                        date_prise_en_charge=date.today(),
                        duree_validite=0
                    )

                    # Calculer les montants
                    montant_total = calculer_montant_total(mutualiste, prestation)
                    montant_pris_en_charge = calculer_montant_pris_en_charge(mutualiste, prestation)

                    # Création de la prestation
                    Prestation.objects.create(
                        prise_en_charge=prise_en_charge,
                        centre_sante=request.user.centre_sante,
                        prestation=prestation.prestation,
                        medecin_traitant=medecin,
                        montant_total=montant_total,
                        montant_pris_en_charge=montant_pris_en_charge,
                        montant_moderateur=montant_total - montant_pris_en_charge,
                        tiers_payant=True,
                        description=description_clinique,
                        statut_validation=True,
                        date_validation=date.today()
                    )

                    return redirect('detail_prise_en_charge', prise_en_charge_id=prise_en_charge.id)

                except Exception as e:
                    # Si une erreur se produit, renvoyer un message d'erreur
                    print(f"Erreur lors de la création de la prise en charge: {e}")
                    return render(request, 'frontoffice/priseencharge/ajouter_prestations.html', {
                        'mutualiste': mutualiste,
                        'prestations': prestations,
                        'medecins': medecins,
                        'error_message': 'Une erreur est survenue lors de la création de la prise en charge.'
                    })

        prestations = CentreSantePrestation.objects.filter(
            centre_sante=request.user.centre_sante,
            prestation__categorie="consultation"
        )
        medecins = MedecinTraitant.objects.filter(centre_sante=request.user.centre_sante)

        return render(request, 'frontoffice/priseencharge/ajouter_prestations.html', {
            'mutualiste': mutualiste,
            'prestations': prestations,
            'medecins': medecins
        })

def ajouter_prescription1(request):
    if request.method == "POST":
        form = PrescriptionForm(request.POST)
        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.save()
            form.save_m2m()  # Enregistre les relations ManyToMany
            return redirect('liste_prescriptions')  # Redirige après l'ajout
    else:
        form = PrescriptionForm()

    return render(request, "prescriptions/ajouter_prescription.html", {"form": form})

def ajouter_prescription2(request: HttpRequest, id: int):
    prise_en_charge = get_object_or_404(PriseEnCharge, id=id)
    
    if request.method == "POST":
        form = PrescriptionForm(request.POST)
        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.prise_en_charge = prise_en_charge  # Affecte la prise en charge
            prescription.save()
            form.save_m2m()  # Enregistre les relations ManyToMany
            return redirect('liste_prescription')  # Redirige après l'ajout
    else:
        form = PrescriptionForm()

    return render(request, "frontoffice/priseencharge/ajouter_prescription.html", {"form": form, "prise_en_charge": prise_en_charge})


def ajouter_prescription3(request, id):
    prise_en_charge = get_object_or_404(PriseEnCharge, id=id)

    if request.method == "POST":
        print("Données POST reçues:", request.POST)  # Affiche les données POST dans la console
        form = PrescriptionForm(request.POST)
        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.prise_en_charge = prise_en_charge  # Associer la prise en charge
            prescription.save()

            # Sauvegarder les médicaments ajoutés
            medicaments = request.POST.getlist('medicaments')  # Liste des médicaments
            print("Médicaments dans POST:", medicaments)  # Vérifie ce qui est envoyé dans les données POST

            for med_id, med_data in medicaments:
                print(f"Traitement du médicament {med_id} avec données {med_data}")
                medicament = Medicament.objects.get(id=med_id)
                quantite = med_data['quantite']
                posologie = med_data['posologie']
                substitution = med_data['substitution']
                
                # Ajouter chaque médicament à la prescription
                prescription.medicaments.add(medicament, through_defaults={'quantite_prescrite': quantite, 'posologie': posologie, 'substitution_possible': substitution})

            form.save_m2m()  # Enregistre les relations ManyToMany pour d'autres champs
            return redirect('liste_prescription')  # Redirige après la soumission
    else:
        form = PrescriptionForm()

    return render(request, "frontoffice/priseencharge/ajouter_prescription.html", {"form": form})

def ajouter_prescription4(request, id):
    prise_en_charge = get_object_or_404(PriseEnCharge, id=id)

    if request.method == "POST":
        print("Données POST reçues:", request.POST)  # Affiche les données POST dans la console
        form = PrescriptionForm(request.POST)
        
        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.prise_en_charge = prise_en_charge  # Associer la prise en charge
            prescription.save()

            # Enregistrement des médicaments associés à la prescription
            for i in range(1, len(request.POST.getlist('medicaments[1][medicament]')) + 1):
                medicament_id = request.POST.get(f'medicaments[{i}][medicament]')
                quantite = request.POST.get(f'medicaments[{i}][quantite]')
                posologie = request.POST.get(f'medicaments[{i}][posologie]')
                substitution = request.POST.get(f'medicaments[{i}][substitution]')

                # Créer ou associer le médicament à la prescription
                medicament = Medicament.objects.get(id=medicament_id)
                # Enregistrement d'un médicament prescrit
                Prescription.objects.create(
                    prescription=prescription,
                    medicament=medicament,
                    quantite=quantite,
                    posologie=posologie,
                    substitution=substitution
                )
            return redirect('liste_prescription')
    else:
        form = PrescriptionForm()

    return render(request, "frontoffice/priseencharge/ajouter_prescription.html", {"form": form})


def ajouter_prestationsex1(request: HttpRequest, id: int):
    prise_en_charge = get_object_or_404(PriseEnCharge, id=id)
    mutualiste = get_object_or_404(Mutualiste, id=prise_en_charge.mutualiste.id)

    # Filtrer les prestations disponibles
    prestations_disponibles = CentreSantePrestation.objects.filter(
        centre_sante=request.user.centre_sante,
        prestation__categorie="analyse"
    )
    medecins = MedecinTraitant.objects.filter(centre_sante=request.user.centre_sante)

    # Création du formset personnalisé
    PrestationFormSet = formset_factory(PrestationForm, extra=1, can_delete=True)

    if request.method == "POST":
        prestation_formset = PrestationFormSet(request.POST)

        print("Erreurs du formset:", prestation_formset.errors)  # 🔥 Affiche toutes les erreurs
        print("Données POST reçues:", request.POST)

        if prestation_formset.is_valid():
            medecin_id = request.POST.get('medecin')
            description_clinique = request.POST.get('description_clinique')
            medecin = get_object_or_404(MedecinTraitant, id=medecin_id)
            prestation_id = request.POST.get('form-0-prestation')  # Récupérer l'ID de la prestation
            
            if prestation_id:
                try:
                    prestation_obj = CentreSantePrestation.objects.get(
                        id=prestation_id,
                        centre_sante=request.user.centre_sante
                    )
                    print("Prestation trouvée:", prestation_obj)
                    # La prestation a été trouvée pour le centre de santé de l'utilisateur
                except CentreSantePrestation.DoesNotExist:
                    print(f"Prestation avec ID {prestation_id} non trouvée pour ce centre de santé")


                montant_total = calculer_montant_total(mutualiste, prestation_obj)
                montant_pris_en_charge = calculer_montant_pris_en_charge(mutualiste, prestation_obj)

                try:
                    obj = Prestation.objects.create(
                        prise_en_charge=prise_en_charge,
                        centre_sante=request.user.centre_sante,
                        prestation=prestation_obj.prestation,
                        medecin_traitant=medecin,
                        montant_total=montant_total,
                        montant_pris_en_charge=montant_pris_en_charge,
                        tiers_payant=True,
                        description=description_clinique,
                        statut_validation=True,
                        date_validation=date.today()
                    )
                    print("Prestation créée avec succès:", obj)
                except Exception as e:
                    print("Erreur lors de la création:", e)

            return redirect('detail_prise_en_charge', prise_en_charge_id=prise_en_charge.id)

    else:
        prestation_formset = PrestationFormSet(form_kwargs={'user': request.user})

    return render(request, 'frontoffice/priseencharge/ajouter_prestationsex.html', {
        'mutualiste': mutualiste,
        'prestations': prestations_disponibles,
        'medecins': medecins,
        'prestation_formset': prestation_formset,
    })


def ajouter_prescriptionbon(request, id):
    prise_en_charge = get_object_or_404(PriseEnCharge, id=id)

    if request.method == "POST":
        prescription_form = PrescriptionForm(request.POST)
        formset = MedicamentPrescrisFormSet(request.POST)

        if prescription_form.is_valid() and formset.is_valid():
            prescription = prescription_form.save(commit=False)
            prescription.prise_en_charge = prise_en_charge
            prescription.save()  # Enregistre la prescription

            medicaments = formset.save(commit=False)
            for medicament in medicaments:
                medicament.prestation_prescription = prescription  # Associer les médicaments à la prescription
                medicament.save()

            return redirect('detail_prise_en_charge', prise_en_charge_id=prise_en_charge.id)
        else:
            print("📌 Erreurs du formulaire Prescription:", prescription_form.errors)
            print("📌 Erreurs du Formset:", formset.errors)

    else:
        prescription_form = PrescriptionForm()
        formset = MedicamentPrescrisFormSet()

    return render(request, 'frontoffice/priseencharge/ajouter_prescription.html', {
        'prescription_form': prescription_form,
        'formset': formset,
    })



def ajouter_prestationsexX(request, id):
    prise_en_charge = get_object_or_404(PriseEnCharge, id=id)
    mutualiste = prise_en_charge.mutualiste  # Récupération du mutualiste lié à la prise en charge
    
    if request.method == "POST":
        print("Données POST reçues :", request.POST)  # Affichage des données POST dans la console
        print("Données FILES reçues :", request.FILES)  # Affichage des fichiers envoyés
        formset = ExamenMedicalFormSet(request.POST, request.FILES, instance=prise_en_charge)
        
        if formset.is_valid():
            examens = formset.save(commit=False)
            for examen in examens:
                examen.prise_en_charge = prise_en_charge
                examen.mutualiste = mutualiste
                examen.centre_sante = request.user.centre_sante
                examen.date_prescription = timezone.now()
                examen.statut = ExamenMedical.StatutExamen.EN_ATTENTE
                examen.save()
            return redirect('detail_prise_en_charge', prise_en_charge_id=prise_en_charge.id)
    else:
        formset = ExamenMedicalFormSet(instance=prise_en_charge)
    
    return render(request, "frontoffice/priseencharge/ajouter_prestationsex.html", {
        "prise_en_charge": prise_en_charge,
        "formset": formset
    })
    
def ajouter_prestationsexBON(request, id):
    prise_en_charge = get_object_or_404(PriseEnCharge, id=id)
    mutualiste = prise_en_charge.mutualiste  # Récupération du mutualiste lié à la prise en charge
    
    if request.method == "POST":
        print("Données POST reçues :", request.POST)  # Affichage des données POST dans la console
        print("Données FILES reçues :", request.FILES)  # Affichage des fichiers envoyés
        formset = ExamenMedicalFormSet(request.POST, request.FILES, instance=prise_en_charge)
        
        if formset.is_valid():
            examens = formset.save(commit=False)
            examens_existants = ExamenMedical.objects.filter(prise_en_charge=prise_en_charge)

            examens_types_existants = set(examens_existants.values_list("type_examen_id", flat=True))

            for examen in examens:
                if examen.type_examen_id in examens_types_existants:
                    messages.error(request, f"L'examen {examen.type_examen} est déjà ajouté.")
                    return render(request, "frontoffice/priseencharge/ajouter_prestationsex.html", {
                        "prise_en_charge": prise_en_charge,
                        "formset": formset
                    })
                
                examen.prise_en_charge = prise_en_charge
                examen.mutualiste = mutualiste
                examen.centre_sante = request.user.centre_sante
                examen.date_prescription = timezone.now()
                examen.statut = ExamenMedical.StatutExamen.EN_ATTENTE
                examen.save()

            messages.success(request, "Examens ajoutés avec succès !")
            return redirect('detail_prise_en_charge', prise_en_charge_id=prise_en_charge.id)  # Vérifie que cette route existe
        
    else:
        formset = ExamenMedicalFormSet(instance=prise_en_charge)
    
    return render(request, "frontoffice/priseencharge/ajouter_prestationsex.html", {
        "prise_en_charge": prise_en_charge,
        "formset": formset
    })
    
def ajouter_prestationsexZ(request, id):
    prise_en_charge = get_object_or_404(PriseEnCharge, id=id)
    mutualiste = prise_en_charge.mutualiste  # Mutualiste lié à la prise en charge

    # Utilisation d'un formset lié aux examens de cette prise en charge
    ExamenMedicalFormSet = modelformset_factory(
        ExamenMedical, form=ExamenMedicalForm, extra=1, can_delete=True
    )

    if request.method == "POST":
        formset = ExamenMedicalFormSet(request.POST, request.FILES, queryset=ExamenMedical.objects.filter(prise_en_charge=prise_en_charge))

        if formset.is_valid():
            examens = formset.save(commit=False)  # Ne pas enregistrer tout de suite

            # Liste des types d'examen déjà ajoutés
            examens_types_existants = set(ExamenMedical.objects.filter(prise_en_charge=prise_en_charge).values_list("type_examen_id", flat=True))

            for examen in examens:
                if examen.type_examen:  # Vérification que le champ est rempli
                    if examen.type_examen_id in examens_types_existants:
                        messages.error(request, f"L'examen {examen.type_examen} est déjà ajouté.")
                        return render(request, "frontoffice/priseencharge/ajouter_prestationsex.html", {
                            "prise_en_charge": prise_en_charge,
                            "formset": formset
                        })

                    # Compléter les informations avant sauvegarde
                    examen.prise_en_charge = prise_en_charge
                    examen.mutualiste = mutualiste
                    examen.centre_sante = request.user.centre_sante
                    examen.date_prescription = timezone.now()
                    examen.statut = ExamenMedical.StatutExamen.EN_ATTENTE
                    examen.save()

            messages.success(request, "Examens ajoutés avec succès !")
            return redirect('detail_prise_en_charge', prise_en_charge_id=prise_en_charge.id) 
        
    else:
        formset = ExamenMedicalFormSet(queryset=ExamenMedical.objects.filter(prise_en_charge=prise_en_charge))

    return render(request, "frontoffice/priseencharge/ajouter_prestationsex.html", {
        "prise_en_charge": prise_en_charge,
        "formset": formset
    })
    


from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import PrestationPharmacie, MedicamentUtilise, Prescription, Medicament
import json

@csrf_exempt
def ajouter_dispensatione(request, id: int):
    # Récupération de la prescription à partir de son ID
    prescription = Prescription.objects.get(id=id)
    
    if request.method == "POST":
        try:
            # Récupérer les données envoyées par le formulaire
            mutualiste_id = request.POST.get("mutualiste_id")

            # Création de la prestation pharmacie
            prestation = PrestationPharmacie.objects.create(
                prescription=prescription,
                mutualiste_id=mutualiste_id,
                centre_sante=prescription.centre_sante
            )

            total_medicaments = 0
            # Parcourir les médicaments et leurs quantités envoyées via le formulaire
            for key, value in request.POST.items():
                if key.startswith("quantite_"):
                    med_id = key.split("_")[1]
                    medicament = Medicament.objects.get(id=med_id)
                    quantite = int(value)
                    cout_unitaire = medicament.prix
                    
                    MedicamentUtilise.objects.create(
                        prestation_pharmacie=prestation,
                        medicament=medicament,
                        quantite_servie=quantite,
                        cout_unitaire=cout_unitaire
                    )

                    total_medicaments += quantite * cout_unitaire

            prestation.calculer_montant_total()  # Calcul du montant total
            prescription.statut = "validée"
            prescription.save()

            return JsonResponse({"status": "success", "message": "Prestation créée avec succès !"})
        
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    # Récupérer les médicaments prescrits pour cette prescription
    medicaments = [
        {
            "id": medicament.medicament.id,
            "nom": medicament.medicament.nom,
            "prix": medicament.medicament.cout_unitaire
        }
        for medicament in prescription.medicaments_prescris.all()
    ]
    
    # Affichage du formulaire avec les médicaments
    return render(request, 'frontoffice/priseencharge/ajouter_dispensation_formulaire.html', {
        'prescription_id': id,
        'medicaments': medicaments,
    })


@csrf_exempt
def ajouter_dispensationbon(request, id: int):
    # Récupération de la prescription à partir de son ID
    prescription = Prescription.objects.get(id=id)
    medicamentl = Medicament.objects.all()
    
    if request.method == "POST":
        try:
            # Récupérer les données envoyées par le formulaire
            mutualiste_id = request.POST.get("mutualiste_id")

            # Création de la prestation pharmacie
            prestation = PrestationPharmacie.objects.create(
                prescription=prescription,
                mutualiste_id=mutualiste_id,
                centre_sante=request.user.centre_sante,
            )

            total_medicaments = 0
            # Parcourir les médicaments et leurs quantités envoyées via le formulaire
            for key, value in request.POST.items():
                if key.startswith("quantite_"):
                    med_id = key.split("_")[1]
                    medicament = Medicament.objects.get(id=med_id)
                    quantite = int(value)

                    # Récupérer le prix envoyé depuis le formulaire
                    prix_key = f"prix_{med_id}"
                    cout_unitaire = float(request.POST.get(prix_key, medicament.cout_unitaire))  # Valeur par défaut = prix du modèle

                    MedicamentUtilise.objects.create(
                        prestation_pharmacie=prestation,
                        medicament=medicament,
                        quantite_servie=quantite,
                        cout_unitaire=cout_unitaire
                    )

                    total_medicaments += quantite * cout_unitaire

            prestation.calculer_montant_total()  # Calcul du montant total
            prescription.statut = "validée"
            prescription.save()

            #return JsonResponse({"status": "success", "message": "Prestation créée avec succès !"})
            return redirect('tableau_de_bord_pharmacie')
        
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    # Récupérer les médicaments prescrits pour cette prescription et leur quantité
    medicaments = []
    for medicament_prescrit in prescription.medicaments_prescris.all():
        medicament = medicament_prescrit.medicament
        quantite_prescrite = medicament_prescrit.quantite_prescrite  # Supposons que `quantite` est stocké dans `medicaments_prescris`

        medicaments.append({
            "id": medicament.id,
            "nom": medicament.nom,
            "prix": medicament.cout_unitaire,
            "quantite": quantite_prescrite
        })
    
    # Affichage du formulaire avec les médicaments et leur quantité
    return render(request, 'frontoffice/priseencharge/ajouter_dispensation_formulaire.html', {
        'prescription_id': id,
        'medicaments': medicaments,
        'prescription' : prescription,
        'medicamentl':medicamentl
    })

#                                           BON
from decimal import Decimal
from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from .models import Prescription, Medicament, PrestationPharmacie, MedicamentUtilise

@csrf_protect
def ajouter_dispensationBOOOOOO(request, id: int):
    # Récupération de la prescription
    prescription = get_object_or_404(Prescription, id=id)
    medicamentl = Medicament.objects.all()

    if request.method == "POST":
        try:
            mutualiste_id = request.POST.get("mutualiste_id")

            if not mutualiste_id:
                return JsonResponse({"status": "error", "message": "Le mutualiste est requis."})

            # Création de la prestation pharmacie
            prestation = PrestationPharmacie.objects.create(
                prescription=prescription,
                mutualiste_id=mutualiste_id,
                centre_sante=request.user.centre_sante,
            )

            total_medicaments = Decimal("0.00")

            for key, value in request.POST.items():
                if key.startswith("quantite_"):
                    try:
                        med_id = key.split("_")[1]
                        medicament = Medicament.objects.get(id=med_id)
                        quantite = int(value)

                        if quantite <= 0:
                            return JsonResponse({"status": "error", "message": f"Quantité invalide pour {medicament.nom}."})

                        prix_key = f"prix_{med_id}"
                        cout_unitaire = Decimal(request.POST.get(prix_key, medicament.cout_unitaire))

                        MedicamentUtilise.objects.create(
                            prestation_pharmacie=prestation,
                            medicament=medicament,
                            quantite_servie=quantite,
                            cout_unitaire=cout_unitaire
                        )

                        total_medicaments += quantite * cout_unitaire
                    
                    except Medicament.DoesNotExist:
                        return JsonResponse({"status": "error", "message": f"Médicament ID {med_id} introuvable."})
                    except ValueError:
                        return JsonResponse({"status": "error", "message": f"Valeur incorrecte pour {med_id}."})

            # Mise à jour du montant total et du statut de la prescription
            prestation.calculer_montant_total()
            prescription.statut = "validée"
            prescription.save()

            return redirect('tableau_de_bord_pharmacie')

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    medicaments = [
        {
            "id": mp.medicament.id,
            "nom": mp.medicament.nom,
            "prix": mp.medicament.cout_unitaire,
            "quantite": mp.quantite_prescrite
        }
        for mp in prescription.medicaments_prescris.all()
    ]

    return render(request, 'frontoffice/priseencharge/ajouter_dispensation_formulaire.html', {
        'prescription_id': id,
        'medicaments': medicaments,
        'prescription': prescription,
        'medicamentl': medicamentl
    })
    
def importer_medicaments1(request):
    if request.method == "POST" and request.FILES['fichier']:
        fichier = request.FILES['fichier']
        try:
            df = pd.read_excel(fichier, engine='openpyxl')
            
            # Vérification des colonnes attendues
            colonnes_attendues = ["code", "nom", "description", "dci", "molecule", "typem", "disponible_en_pharmacie", "cout_unitaire","regime"]
            if not all(col in df.columns for col in colonnes_attendues):
                raise ValidationError("Le fichier ne contient pas toutes les colonnes requises.")

            # Importation des données
            for index, row in df.iterrows():
                Medicament.objects.update_or_create(
                    code=row["code"],
                    defaults={
                        "nom": row["nom"],
                        "description": row.get("description", ""),
                        "dci": row.get("dci", ""),
                        "molecule": row.get("molecule", ""),
                        "typem": row.get("typem", ""),
                        "disponible_en_pharmacie": row["disponible_en_pharmacie"],
                        "cout_unitaire": row["cout_unitaire"],
                        "regime": row["regime"],
                    }
                )
            messages.success(request, "Importation réussie !")
        except Exception as e:
            messages.error(request, f"Erreur lors de l'importation : {str(e)}")
    return redirect('liste_medicament')

import pandas as pd
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import Medicament

import pandas as pd
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import Medicament

def importer_medicaments2(request):
    if request.method == "POST" and request.FILES.get("fichier"):
        fichier = request.FILES["fichier"]
        print(fichier)  # Debug: vérifier le fichier reçu
        try:
            df = pd.read_excel(fichier, engine="openpyxl")
            print(df)  # Debug: vérifier la lecture du fichier

            # Colonnes attendues
            colonnes_attendues = [
                "code", "nom", "description", "dci", "molecule",
                "typem", "disponible_en_pharmacie", "cout_unitaire", "regime"
            ]

            # Vérification des colonnes
            if not all(col in df.columns for col in colonnes_attendues):
                raise ValidationError("🚨 Le fichier ne contient pas toutes les colonnes requises.")

            # Nettoyage des données
            df.fillna({"description": "", "dci": "", "molecule": "", "typem": ""}, inplace=True)
            df["nom"] = df["nom"].astype(str).str.strip()
            df["description"] = df["description"].astype(str).str.strip()
            df["cout_unitaire"] = pd.to_numeric(df["cout_unitaire"], errors="coerce").fillna(0)
            df["regime"] = pd.to_numeric(df["regime"], errors="coerce").fillna(0).astype(int)
            df["disponible_en_pharmacie"] = df["disponible_en_pharmacie"].astype(str).str.lower().isin(["true", "1", "oui"]).astype(int)

            # Vérification et importation des médicaments
            for index, row in df.iterrows():
                try:
                    # Vérifier que les champs obligatoires ne sont pas vides
                    if not row["code"] or not row["nom"]:
                        raise ValueError(f"Ligne {index + 1} : Code ou nom du médicament manquant.")

                    # Mise à jour ou création du médicament
                    Medicament.objects.update_or_create(
                        code=row["code"],
                        defaults={
                            "nom": row["nom"],
                            "description": row["description"],
                            "dci": row["dci"],
                            "molecule": row["molecule"],
                            "typem": row["typem"],
                            "disponible_en_pharmacie": row["disponible_en_pharmacie"],
                            "cout_unitaire": row["cout_unitaire"],
                            "regime": row["regime"],
                        }
                    )

                except ValueError as ve:
                    messages.warning(request, f"⚠️ Erreur ligne {index + 1} : {ve}")

            messages.success(request, "✅ Importation réussie !")

        except ValidationError as ve:
            messages.error(request, f"🚨 Erreur de validation : {ve}")
        except Exception as e:
            messages.error(request, f"❌ Erreur lors de l'importation : {str(e)}")

    return redirect("liste_medicament")



from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Prestation, PrestationPharmacie  # Importe tes modèles

def prestations_pdfL(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="prestations.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    y_position = height - 50  # Position initiale en haut de la page

    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, y_position, "Rapport des Prestations")
    y_position -= 40

    date_str = request.GET.get("date", "")
    if date_str:
        date_obj = timezone.make_aware(datetime.strptime(date_str, "%Y-%m-%d"))
        debut_mois = date_obj.replace(day=1, hour=0, minute=0, second=0)
        fin_mois = (debut_mois + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

        prestations = Prestation.objects.filter(date_prestation__range=(debut_mois, fin_mois))
        prestations_pharmacie = PrestationPharmacie.objects.filter(date_prestation__range=(debut_mois, fin_mois))

        categories = {
            "Hospitalisation": prestations.filter(prestation__categorie='hospitalisation'),
            "Optique": prestations.filter(prestation__categorie='optique'),
            "Autres": prestations.exclude(prestation__categorie__in=['hospitalisation', 'optique']),
            "Pharmacie": prestations_pharmacie,
        }

        p.setFont("Helvetica", 12)
        for categorie, prestations_list in categories.items():
            p.setFont("Helvetica-Bold", 14)
            p.drawString(50, y_position, categorie)
            y_position -= 20

            p.setFont("Helvetica", 10)
            for prestation in prestations_list:
                centre_sante = prestation.centre_sante if hasattr(prestation, 'centre_sante') else "N/A"
                date_prestation = prestation.date_prestation.strftime("%d-%m-%Y")
                montant_total = prestation.montant_total if hasattr(prestation, 'montant_total') else "N/A"

                ligne = f"- {centre_sante} | {date_prestation} | {montant_total} FCFA"
                p.drawString(60, y_position, ligne)
                y_position -= 15

                if y_position < 50:  # Gérer le changement de page
                    p.showPage()
                    p.setFont("Helvetica", 12)
                    y_position = height - 50

            y_position -= 10

    p.showPage()
    p.save()
    return response

from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from datetime import datetime, timedelta
from django.utils import timezone
import os
from .models import Prestation, PrestationPharmacie


def prestations_pdfT(request):
    # Définir la réponse HTTP pour le fichier PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="prestations.pdf"'

    # Définition du document PDF
    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    width, height = A4

    # Chargement du logo
    logo_path = os.path.join("static", "img", "logo.png")  # Modifier avec le bon chemin
    if os.path.exists(logo_path):
        logo = ImageReader(logo_path)
        elements.append(logo)

    # Ajout du titre
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    styles = getSampleStyleSheet()
    title = Paragraph("<b>Rapport des Prestations</b>", styles["Title"])
    elements.append(title)

    # Récupération de la date
    date_str = request.GET.get("date", "")
    if date_str:
        date_obj = timezone.make_aware(datetime.strptime(date_str, "%Y-%m-%d"))
        debut_mois = date_obj.replace(day=1, hour=0, minute=0, second=0)
        fin_mois = (debut_mois + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

        prestations = Prestation.objects.filter(date_prestation__range=(debut_mois, fin_mois))
        prestations_pharmacie = PrestationPharmacie.objects.filter(date_prestation__range=(debut_mois, fin_mois))

        categories = {
            "Hospitalisation": prestations.filter(prestation__categorie='hospitalisation'),
            "Optique": prestations.filter(prestation__categorie='optique'),
            "Autres": prestations.exclude(prestation__categorie__in=['hospitalisation', 'optique']),
            "Pharmacie": prestations_pharmacie,
        }

        # Création du tableau
        table_data = [["Catégorie", "Centre de Santé", "Date", "Montant (FCFA)"]]
        for categorie, prestations_list in categories.items():
            for prestation in prestations_list:
                centre_sante = getattr(prestation, 'centre_sante', "N/A")
                date_prestation = prestation.date_prestation.strftime("%d-%m-%Y")
                montant_total = getattr(prestation, 'montant_total', "N/A")
                table_data.append([categorie, centre_sante, date_prestation, montant_total])

        # Style du tableau
        table = Table(table_data, colWidths=[100, 150, 80, 80])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        elements.append(table)

    # Générer le PDF
    doc.build(elements)
    return response


from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Prestation, PrestationPharmacie

def prestations_pdfLS(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="prestations.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    y_position = height - 50  # Position initiale en haut de la page

    # ✅ Ajouter un logo
    logo_path = "static/backoffice/img/logo/logo.png"  # Assure-toi que le logo est accessible
    p.drawImage(ImageReader(logo_path), 50, height - 80, width=80, height=50, mask='auto')

    # ✅ Titre du rapport
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, height - 50, "Rapport des Prestations")
    y_position -= 60

    date_str = request.GET.get("date", "")
    if date_str:
        date_obj = timezone.make_aware(datetime.strptime(date_str, "%Y-%m-%d"))
        debut_mois = date_obj.replace(day=1, hour=0, minute=0, second=0)
        fin_mois = (debut_mois + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

        prestations = Prestation.objects.filter(date_prestation__range=(debut_mois, fin_mois))
        prestations_pharmacie = PrestationPharmacie.objects.filter(date_prestation__range=(debut_mois, fin_mois))

        # ✅ Grouper les prestations par centre de santé et calculer les sommes
        centres = {}
        for prestation in prestations:
            centre = prestation.centre_sante.nom if prestation.centre_sante else "Inconnu"
            if centre not in centres:
                centres[centre] = {"total": 0, "pris_en_charge": 0, "moderateur": 0}

            centres[centre]["total"] += prestation.montant_total
            centres[centre]["pris_en_charge"] += prestation.montant_pris_en_charge
            centres[centre]["moderateur"] += prestation.montant_moderateur

        for prestation in prestations_pharmacie:
            centre = prestation.centre_sante.nom if prestation.centre_sante else "Inconnu"
            if centre not in centres:
                centres[centre] = {"total": 0, "pris_en_charge": 0, "moderateur": 0}

            centres[centre]["total"] += prestation.montant_total
            centres[centre]["pris_en_charge"] += prestation.part_mutuelle
            centres[centre]["moderateur"] += prestation.part_mutualiste

        # ✅ Afficher les totaux par centre de santé
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y_position, "Sommes totales par centre de santé")
        y_position -= 20

        p.setFont("Helvetica", 10)
        for centre, data in centres.items():
            ligne = f"{centre}: {data['total']} FCFA | Pris en charge: {data['pris_en_charge']} FCFA | Modérateur: {data['moderateur']} FCFA"
            p.drawString(60, y_position, ligne)
            y_position -= 15

            if y_position < 50:  # Gérer la pagination
                p.showPage()
                p.setFont("Helvetica", 10)
                y_position = height - 50

    p.showPage()
    p.save()
    return response

from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Prestation, PrestationPharmacie

def prestations_pdfok(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="prestations.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    y_position = height - 50  

    # ✅ Ajout du logo
    logo_path = "static/backoffice/img/logo/logo.png"
    p.drawImage(ImageReader(logo_path), 50, height - 80, width=80, height=50, mask='auto')

    # ✅ Titre du rapport
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, height - 50, "Rapport des Prestations")
    y_position -= 60

    date_str = request.GET.get("date", "")
    if date_str:
        date_obj = timezone.make_aware(datetime.strptime(date_str, "%Y-%m-%d"))
        debut_mois = date_obj.replace(day=1, hour=0, minute=0, second=0)
        fin_mois = (debut_mois + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

        prestations = Prestation.objects.filter(date_prestation__range=(debut_mois, fin_mois))
        prestations_pharmacie = PrestationPharmacie.objects.filter(date_prestation__range=(debut_mois, fin_mois))

        # ✅ Catégorisation des prestations
        categories = {
            "Hospitalisation": prestations.filter(prestation__categorie='hospitalisation'),
            "Optique": prestations.filter(prestation__categorie='optique'),
            "Ambulatoires": prestations.exclude(prestation__categorie__in=['hospitalisation', 'optique']),
            "Pharmacie": prestations_pharmacie,
        }

        # ✅ Initialisation du tableau pour l'affichage des données
        table_data = [["Catégorie", "Centre de Santé", "Total (FCFA)", "Pris en charge (FCFA)", "Modérateur (FCFA)"]]

        # ✅ Traitement des prestations par catégorie
        for categorie, prestations_list in categories.items():
            centres = {}

            for prestation in prestations_list:
                centre = prestation.centre_sante.nom if hasattr(prestation, 'centre_sante') and prestation.centre_sante else "Inconnu"
                if centre not in centres:
                    centres[centre] = {"total": 0, "pris_en_charge": 0, "moderateur": 0}

                centres[centre]["total"] += getattr(prestation, 'montant_total', 0)
                centres[centre]["pris_en_charge"] += getattr(prestation, 'montant_pris_en_charge', 0) or getattr(prestation, 'part_mutuelle', 0)
                centres[centre]["moderateur"] += getattr(prestation, 'montant_moderateur', 0) or getattr(prestation, 'part_mutualiste', 0)

            # ✅ Ajout des données au tableau
            for centre, data in centres.items():
                table_data.append([categorie, centre, data["total"], data["pris_en_charge"], data["moderateur"]])

        # ✅ Création du tableau avec reportlab
        table = Table(table_data, colWidths=[100, 150, 80, 80, 80])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 12),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ]))

        # ✅ Positionnement du tableau sur le PDF
        table.wrapOn(p, width, height)
        table.drawOn(p, 30, y_position - len(table_data) * 20)

    p.showPage()
    p.save()
    return response

from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Prestation, PrestationPharmacie

def prestations_pdfOKbon(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="prestations.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # ✅ Ajout du logo
    logo_path = "static/backoffice/img/logo/logo.png"
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("<b>Rapport des sinstres</b>", styles["Title"]))
    elements.append(Spacer(1, 10))

    # ✅ Récupération de la date
    date_str = request.GET.get("date", "")
    if date_str:
        date_obj = timezone.make_aware(datetime.strptime(date_str, "%Y-%m-%d"))
        debut_mois = date_obj.replace(day=1, hour=0, minute=0, second=0)
        fin_mois = (debut_mois + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

        prestations = Prestation.objects.filter(date_prestation__range=(debut_mois, fin_mois))
        prestations_pharmacie = PrestationPharmacie.objects.filter(date_prestation__range=(debut_mois, fin_mois))

        # ✅ Catégorisation des prestations
        categories = {
            "Hospitalisation": prestations.filter(prestation__categorie='hospitalisation'),
            "Optique": prestations.filter(prestation__categorie='optique'),
            "Ambulatoires": prestations.exclude(prestation__categorie__in=['hospitalisation', 'optique']),
            "Pharmacie": prestations_pharmacie,
        }

        for categorie, prestations_list in categories.items():
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(f"<b>{categorie}</b>", styles["Heading2"]))

            table_data = [["Centre de Santé", "Total", "Mutuelle", "Mutualiste"]]
            centres = {}

            for prestation in prestations_list:
                centre = prestation.centre_sante.nom if hasattr(prestation, 'centre_sante') and prestation.centre_sante else "Inconnu"
                if centre not in centres:
                    centres[centre] = {"total": 0, "pris_en_charge": 0, "moderateur": 0}

                centres[centre]["total"] += getattr(prestation, 'montant_total', 0)
                centres[centre]["pris_en_charge"] += getattr(prestation, 'montant_pris_en_charge', 0) or getattr(prestation, 'part_mutuelle', 0)
                centres[centre]["moderateur"] += getattr(prestation, 'montant_moderateur', 0) or getattr(prestation, 'part_mutualiste', 0)

            for centre, data in centres.items():
                table_data.append([
                centre, 
                "{:,.0f}".format(data['total']).replace(",", " "), 
                "{:,.0f}".format(data['pris_en_charge']).replace(",", " "), 
                "{:,.0f}".format(data['moderateur']).replace(",", " ")
            ])


            table = Table(table_data, colWidths=[150, 80, 80, 80])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]))

            elements.append(table)

    doc.build(elements)
    return response


from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image

def prestations_pdfOKbonSom(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="prestations.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # ✅ Ajout du logo
    logo_path = "static/backoffice/img/logo/logo.png"
    elements.append(Image(logo_path, width=100, height=50))  # Assurez-vous que le chemin est correct
    elements.append(Spacer(1, 20))

    # ✅ Récupération de la date
    date_str = request.GET.get("date", "")
    if date_str:
        try:
            date_obj = timezone.make_aware(datetime.strptime(date_str, "%Y-%m-%d"))
            debut_mois = date_obj.replace(day=1, hour=0, minute=0, second=0)
            fin_mois = (debut_mois + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

            mois_annee = debut_mois.strftime("%B %Y").capitalize()
            elements.append(Paragraph(f"<b>Rapport des sinistres - {mois_annee}</b>", styles["Title"]))
            elements.append(Spacer(1, 10))

            prestations = Prestation.objects.filter(date_prestation__range=(debut_mois, fin_mois))
            prestations_pharmacie = PrestationPharmacie.objects.filter(date_prestation__range=(debut_mois, fin_mois))

            if not prestations.exists() and not prestations_pharmacie.exists():
                elements.append(Paragraph("Aucune prestation trouvée pour cette période.", styles["BodyText"]))
            else:
                # ✅ Catégorisation des prestations
                categories = {
                    "Hospitalisation": prestations.filter(prestation__categorie='hospitalisation'),
                    "Optique": prestations.filter(prestation__categorie='optique'),
                    "Ambulatoires": prestations.exclude(prestation__categorie__in=['hospitalisation', 'optique']),
                    "Pharmacie": prestations_pharmacie,
                }

                for categorie, prestations_list in categories.items():
                    if prestations_list.exists():
                        elements.append(Spacer(1, 10))
                        elements.append(Paragraph(f"<b>{categorie}</b>", styles["Heading2"]))

                        table_data = [["Centre de Santé", "Total", "Mutuelle", "Mutualiste"]]
                        centres = {}

                        for prestation in prestations_list:
                            centre = prestation.centre_sante.nom if hasattr(prestation, 'centre_sante') and prestation.centre_sante else "Inconnu"
                        if centre not in centres:
                            centres[centre] = {"total": 0, "pris_en_charge": 0, "moderateur": 0}

                        centres[centre]["total"] += getattr(prestation, 'montant_total', 0)
                        centres[centre]["pris_en_charge"] += getattr(prestation, 'montant_pris_en_charge', 0) or getattr(prestation, 'part_mutuelle', 0)
                        centres[centre]["moderateur"] += getattr(prestation, 'montant_moderateur', 0) or getattr(prestation, 'part_mutualiste', 0)

                        for centre, data in centres.items():
                            table_data.append([
                                centre, 
                                "{:,.0f}".format(data['total']).replace(",", " "), 
                                "{:,.0f}".format(data['pris_en_charge']).replace(",", " "), 
                                "{:,.0f}".format(data['moderateur']).replace(",", " ")
                            ])

                        table = Table(table_data, colWidths=[150, 80, 80, 80])
                        table.setStyle(TableStyle([
                            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, 0), 12),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                            ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ]))

                        elements.append(table)

        except ValueError:
            elements.append(Paragraph("<b>Format de date invalide. Veuillez utiliser AAAA-MM-JJ.</b>", styles["BodyText"]))
    
    else:
        elements.append(Paragraph("<b>Aucune date fournie. Veuillez spécifier une date.</b>", styles["BodyText"]))

    doc.build(elements)
    return response
#                                            BOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO




from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from reportlab.lib.pagesizes import A4 # type: ignore
from reportlab.pdfgen import canvas # type: ignore
from io import BytesIO
from .models import Prescription, Medicament, PrestationPharmacie, MedicamentUtilise

@csrf_exempt
def ajouter_dispensationtext(request, id: int):
    prescription = Prescription.objects.get(id=id)
    medicamentl = Medicament.objects.all()
    
    if request.method == "POST":
        try:
            mutualiste_id = request.POST.get("mutualiste_id")

            prestation = PrestationPharmacie.objects.create(
                prescription=prescription,
                mutualiste_id=mutualiste_id,
                centre_sante=request.user.centre_sante,
            )

            total_medicaments = 0
            medicaments_utilises = []

            for key, value in request.POST.items():
                if key.startswith("quantite_"):
                    med_id = key.split("_")[1]
                    medicament = Medicament.objects.get(id=med_id)
                    quantite = int(value)
                    prix_key = f"prix_{med_id}"
                    cout_unitaire = float(request.POST.get(prix_key, medicament.cout_unitaire))

                    MedicamentUtilise.objects.create(
                        prestation_pharmacie=prestation,
                        medicament=medicament,
                        quantite_servie=quantite,
                        cout_unitaire=cout_unitaire
                    )

                    medicaments_utilises.append({
                        "nom": medicament.nom,
                        "quantite": quantite,
                        "prix_unitaire": cout_unitaire,
                        "total": quantite * cout_unitaire
                    })

                    total_medicaments += quantite * cout_unitaire

            prestation.calculer_montant_total()
            prescription.statut = "validée"
            prescription.save()

            return generer_pdf_dispensation(prescription, prestation, medicaments_utilises)

        except Exception as e:
            return HttpResponse(f"Erreur : {str(e)}", content_type="text/plain")

    medicaments = [{
        "id": medicament_prescrit.medicament.id,
        "nom": medicament_prescrit.medicament.nom,
        "prix": medicament_prescrit.medicament.cout_unitaire,
        "quantite": medicament_prescrit.quantite_prescrite
    } for medicament_prescrit in prescription.medicaments_prescris.all()]

    return render(request, 'frontoffice/priseencharge/ajouter_dispensation_formulaire.html', {
        'prescription_id': id,
        'medicaments': medicaments,
        'prescription': prescription,
        'medicamentl': medicamentl
    })
    
    
def valider_matriculeBON24Mars(request):
    matricule = request.GET.get('matricule')
    
    if not matricule:
        return JsonResponse({"status": "error", "message": "Le matricule est requis."}, status=400)
    
    try:
        print(f"🔍 Matricule recherché : {matricule}")
        
        # Vérifiez si le matricule correspond à un mutualiste
        mutualiste = Mutualiste.objects.filter(code_matricule=matricule).first()
        if mutualiste:
            return JsonResponse({
                "status": "success",
                "type": "mutualiste",
                "data": {
                    'id': mutualiste.id,
                    "nom": mutualiste.nom,
                    "prenom": mutualiste.prenom,
                    "age": mutualiste.age,
                    "photo": mutualiste.photo.url if mutualiste.photo else None,
                }
            })

        # Vérifiez si le matricule correspond à un bénéficiaire
        beneficiaire = Beneficiaire.objects.filter(code_matricule=matricule).first()
        if beneficiaire:
            return JsonResponse({
                "status": "success",
                "type": "beneficiaire",
                "data": {
                    'id': beneficiaire.id,
                    "nom": beneficiaire.nom,
                    "prenom": beneficiaire.prenom,
                    "age": beneficiaire.age,
                    "photo": beneficiaire.photo.url if beneficiaire.photo else None,
                }
            })

        # Si aucun des deux n'est trouvé
        return JsonResponse({"status": "error", "message": "Matricule non trouvé."}, status=404)
    
    except Exception as e:
        return JsonResponse({"status": "error", "message": f"Une erreur est survenue : {str(e)}"}, status=500)

def valider_matriculeT(request):
    matricule = request.GET.get('matricule')
    
    if not matricule: 
        return JsonResponse({"status": "error", "message": "Le matricule est requis."}, status=400)
    
    try:
        # Vérifiez si le matricule correspond à un mutualiste
        mutualiste = Mutualisteliste.objects.filter(code_matricule=matricule).first()
        if mutualiste:
            return JsonResponse({
                "status": "success",
                "type": "mutualiste",
                "data": {
                    'id': mutualiste.id,
                    "nom": mutualiste.nom,
                    "prenom": mutualiste.prenom,
                    "age": mutualiste.age,
                    "photo": mutualiste.photo.url if mutualiste.photo else None,
                }
            })

        # Vérifiez si le matricule correspond à un bénéficiaire
        beneficiaire = Beneficiaire.objects.filter(code_matricule=matricule).first()
        if beneficiaire:
            return JsonResponse({
                "status": "success",
                "type": "beneficiaire",
                "data": {
                    'id': beneficiaire.id,
                    "nom": beneficiaire.nom,
                    "prenom": beneficiaire.prenom,
                    "age": beneficiaire.age,
                    "photo": beneficiaire.photo.url if beneficiaire.photo else None,
                }
            })

        # Si aucun des deux n'est trouvé
        return JsonResponse({"status": "error", "message": "Matricule non trouvé."}, status=404)
    
    except Exception as e:
        return JsonResponse({"status": "error", "message": f"Une erreur est survenue : {str(e)}"}, status=500)
    

def ajouter_prestationsbon(request: HttpRequest, id: int):
    mutualiste = get_object_or_404(Mutualiste, id=id)

    if request.method == "POST":
        print(request.POST)  # 🔍 Debug : Vérifier le contenu du POST
        prestation_id = request.POST.get('prestation')  # Récupérer une seule prestation
        medecin_id = request.POST.get('medecin')  # Récupérer le médecin
        description_clinique = request.POST.get('description_clinique')

        if prestation_id:  # Vérifier si une prestation a été sélectionnée
            prestation = get_object_or_404(CentreSantePrestation, prestation=prestation_id,centre_sante=request.user.centre_sante)
            medecin = get_object_or_404(MedecinTraitant, id=medecin_id)  # Récupérer le médecin par son ID
            duree_validite = calculer_duree_validite(mutualiste)
            
            # Création de la prise en charge
            prise_en_charge = PriseEnCharge.objects.create(
                mutualiste=mutualiste,
                centre=request.user.centre_sante,
                date_prise_en_charge=date.today(),
                duree_validite=duree_validite
            )

            # Calculer le montant selon la logique métier du mutualiste
            montant_total = calculer_montant_total(mutualiste, prestation)  # Fonction à définir
            montant_pris_en_charge = calculer_montant_pris_en_charge(mutualiste, prestation)  # Fonction à définir

            # Création de la prestation réalisée avec `statut_validation=True`
            Prestation.objects.create(
                prise_en_charge=prise_en_charge,
                centre_sante=request.user.centre_sante,
                prestation=prestation.prestation,  # Prend la prestation liée
                medecin_traitant=medecin,  # L'objet médecin traitant
                montant_total=montant_total,
                montant_pris_en_charge=montant_pris_en_charge,
                montant_moderateur=montant_total - montant_pris_en_charge,
                tiers_payant=True,
                description=description_clinique,
                statut_validation=True,  # ⚡ Validation automatique
                date_validation=date.today()
            )

        # return redirect('prise_en_charge')  # Rediriger après soumission
        # Rediriger vers la page de détail de la prise en charge
        return redirect('detail_prise_en_charge', prise_en_charge_id=prise_en_charge.id)

    # Si c'est une méthode GET (ou autre), afficher le formulaire
    prestations = CentreSantePrestation.objects.filter(
        centre_sante=request.user.centre_sante,
        prestation__categorie="consultation"
    )
    medecins = MedecinTraitant.objects.filter(
        centre_sante=request.user.centre_sante
    )

    return render(request, 'frontoffice/priseencharge/ajouter_prestations.html', {
        'mutualiste': mutualiste,
        'prestations': prestations,
        'medecins': medecins
    })
    
    
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
import tempfile
from .models import PriseEnCharge, Prestation  # Assure-toi d'importer tes modèles

def telecharger_prise_en_charge_pdfB(request, id):
    # Récupération de la prise en charge et des prestations associées
    prise_en_charge = get_object_or_404(PriseEnCharge, id=id)
    prestations = Prestation.objects.filter(prise_en_charge=prise_en_charge)

    # Calcul des totaux
    total_prestations = sum(prestation.montant_total for prestation in prestations)
    total_part_mutuelle = sum(prestation.montant_pris_en_charge for prestation in prestations)
    total_part_mutualiste = sum(prestation.montant_moderateur for prestation in prestations)

    # Contexte pour le template
    context = {
        "prise_en_charge": prise_en_charge,
        "prestations": prestations,
        "totalPrestations": total_prestations,
        "totalPartMutuelle": total_part_mutuelle,
        "totalPartMutualiste": total_part_mutualiste
    }

    # Rendu du template HTML
    html_string = render_to_string('frontoffice/priseencharge/pdf_template.html', context)

    # Génération du PDF temporaire
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Prise_en_Charge_{prise_en_charge.id}.pdf"'

    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        HTML(string=html_string).write_pdf(temp_file.name)
        temp_file.seek(0)
        response.write(temp_file.read())

    return response


def ajouter_prestationssys(request: HttpRequest, id: int):
    mutualiste = get_object_or_404(Mutualiste, id=id)
    nature = get_object_or_404(NaturePriseEnCharge, nature='Médicale')

    # Récupérer la dernière prise en charge du mutualiste
    last_prise_en_charge = PriseEnCharge.objects.filter(
        mutualiste=mutualiste, 
        nature=nature
    ).order_by('-date_prise_en_charge').first()

    # Vérifier si la prise en charge est encore valide pour le centre connecté
    if last_prise_en_charge and last_prise_en_charge.duree_validite > 0:
        if last_prise_en_charge.centre == request.user.centre_sante:
            return redirect('detail_prise_en_charge', prise_en_charge_id=last_prise_en_charge.id)
        else:
            # Rediriger vers une page où l'utilisateur peut uniquement ajouter des prestations
            return redirect('ajouter_prestations_autorisees', prise_en_charge_id=last_prise_en_charge.id)

    # Vérifier que l'utilisateur est bien rattaché à un centre de santé
    if not hasattr(request.user, 'centre_sante'):
        return redirect('error_page')  # Redirection vers une page d'erreur

    if request.method == "POST":
        prestation_id = request.POST.get('prestation')
        medecin_id = request.POST.get('medecin')
        description_clinique = request.POST.get('description_clinique')

        if prestation_id and medecin_id:
            prestation = get_object_or_404(
                CentreSantePrestation, 
                prestation_id=prestation_id, 
                centre_sante=request.user.centre_sante
            )
            medecin = get_object_or_404(MedecinTraitant, id=medecin_id)

            duree_validite = calculer_duree_validite(mutualiste)

            # Création de la prise en charge
            prise_en_charge = PriseEnCharge.objects.create(
                mutualiste=mutualiste,
                medecin_traitant=medecin,
                centre=request.user.centre_sante,
                date_prise_en_charge=date.today(),
                duree_validite=duree_validite
            )

            # Calcul du montant
            montant_total = calculer_montant_total(mutualiste, prestation)
            montant_pris_en_charge = calculer_montant_pris_en_charge(mutualiste, prestation)
            montant_moderateur = montant_total - montant_pris_en_charge  

            # Création de la prestation
            Prestation.objects.create(
                prise_en_charge=prise_en_charge,
                centre_sante=request.user.centre_sante,
                prestation=prestation.prestation,
                medecin_traitant=medecin,
                montant_total=montant_total,
                montant_pris_en_charge=montant_pris_en_charge,
                montant_moderateur=montant_moderateur,
                tiers_payant=True,
                description=description_clinique,
                statut_validation=True,
                date_validation=date.today()
            )

            # Gestion de la facture
            mois_actuel = now().month
            annee_actuelle = now().year
            facture, created = Facture.objects.get_or_create(
                centre=request.user.centre_sante,
                defaults={'total_mutualiste': 0, 'total_mutuelle': 0, 'total_general': 0}
            )

            # Mise à jour des montants
            facture.total_mutualiste += montant_moderateur
            facture.total_mutuelle += montant_pris_en_charge
            facture.total_general = facture.total_mutualiste + facture.total_mutuelle
            facture.save()

            return redirect('detail_prise_en_charge', prise_en_charge_id=prise_en_charge.id)

    # Si requête GET, afficher le formulaire
    prestations = CentreSantePrestation.objects.filter(
        centre_sante=request.user.centre_sante,
        prestation__categorie="consultation"
    )
    medecins = MedecinTraitant.objects.filter(
        centre_sante=request.user.centre_sante
    )

    return render(request, 'frontoffice/priseencharge/ajouter_prestations.html', {
        'mutualiste': mutualiste,
        'prestations': prestations,
        'medecins': medecins
    })
    
def ajouter_prestationsexBON26MARS(request, id):
    prise_en_charge = get_object_or_404(PriseEnCharge, id=id)
    mutualiste = prise_en_charge.mutualiste  # Mutualiste lié à la prise en charge

    # Correction : Utilisation de modelformset_factory pour activer .save()
    ExamenMedicalFormSet = modelformset_factory(ExamenMedical, form=ExamenMedicalForm, extra=1, can_delete=False)

    if request.method == "POST":
        print("Données POST reçues :", request.POST)  # Debug
        print("Données FILES reçues :", request.FILES)  # Debug

        formset = ExamenMedicalFormSet(request.POST, request.FILES, queryset=ExamenMedical.objects.filter(prise_en_charge=prise_en_charge))

        if formset.is_valid():
            examens = formset.save(commit=False)  # Correction ici !

            examens_existants = ExamenMedical.objects.filter(prise_en_charge=prise_en_charge)
            examens_types_existants = set(examens_existants.values_list("type_examen_id", flat=True))

            for examen in examens:
                if examen.type_examen:  # Vérifie que le champ est rempli
                    if examen.type_examen_id in examens_types_existants:
                        messages.error(request, f"L'examen {examen.type_examen} est déjà ajouté.")
                        return render(request, "frontoffice/priseencharge/ajouter_prestationsex.html", {
                            "prise_en_charge": prise_en_charge,
                            "formset": formset
                        })

                    # Assigner les informations nécessaires avant l'enregistrement
                    examen.prise_en_charge = prise_en_charge
                    examen.mutualiste = mutualiste
                    examen.centre_sante = request.user.centre_sante
                    examen.date_prescription = timezone.now()
                    examen.statut = ExamenMedical.StatutExamen.EN_ATTENTE
                    examen.save()

            messages.success(request, "Examens ajoutés avec succès !")
            return redirect('detail_prise_en_charge', prise_en_charge_id=prise_en_charge.id)

    else:
        formset = ExamenMedicalFormSet(queryset=ExamenMedical.objects.none())  # Formulaires vides

    return render(request, "frontoffice/priseencharge/ajouter_prestationsex.html", {
        "prise_en_charge": prise_en_charge,
        "formset": formset
    })
    
def ajouter_prestationsex_beneficiaireBON26MARS(request, id):
    prise_en_charge = get_object_or_404(PriseEnCharge, id=id)
    mutualiste = prise_en_charge.beneficiaire  # Mutualiste lié à la prise en charge

    # Correction : Utilisation de modelformset_factory pour activer .save()
    ExamenMedicalFormSet = modelformset_factory(ExamenMedical, form=ExamenMedicalForm, extra=1, can_delete=False)

    if request.method == "POST":
        print("Données POST reçues :", request.POST)  # Debug
        print("Données FILES reçues :", request.FILES)  # Debug

        formset = ExamenMedicalFormSet(request.POST, request.FILES, queryset=ExamenMedical.objects.filter(prise_en_charge=prise_en_charge))

        if formset.is_valid():
            examens = formset.save(commit=False)  # Correction ici !

            examens_existants = ExamenMedical.objects.filter(prise_en_charge=prise_en_charge)
            examens_types_existants = set(examens_existants.values_list("type_examen_id", flat=True))

            for examen in examens:
                if examen.type_examen:  # Vérifie que le champ est rempli
                    if examen.type_examen_id in examens_types_existants:
                        messages.error(request, f"L'examen {examen.type_examen} est déjà ajouté.")
                        return render(request, "frontoffice/priseencharge/ajouter_prestationsex.html", {
                            "prise_en_charge": prise_en_charge,
                            "formset": formset
                        })

                    # Assigner les informations nécessaires avant l'enregistrement 
                    examen.prise_en_charge = prise_en_charge
                    examen.mutualiste = mutualiste.mutualiste
                    examen.beneficiaire = mutualiste
                    examen.centre_sante = request.user.centre_sante
                    examen.date_prescription = timezone.now()
                    examen.statut = ExamenMedical.StatutExamen.EN_ATTENTE
                    examen.save()

            messages.success(request, "Examens ajoutés avec succès !")
            return redirect('detail_prise_en_charge', prise_en_charge_id=prise_en_charge.id)

    else:
        formset = ExamenMedicalFormSet(queryset=ExamenMedical.objects.none())  # Formulaires vides

    return render(request, "frontoffice/priseencharge/ajouter_prestationsex.html", {
        "prise_en_charge": prise_en_charge,
        "formset": formset
    })

    