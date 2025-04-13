from django.shortcuts import render

from cotisations.models import Cotisation
from .models import Beneficiaire, Mutualiste, Mutualisteliste, NaturePrestationSociale, PrestationSociale
from django.shortcuts import render, redirect
from .forms import MutualisteForm, BeneficiaireFormSet, PrestationSociale_tts_Form
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import NaturePrestationSocialeForm, PrestationSocialeForm
from django.contrib.auth.decorators import login_required

from utilisateurs.models import Utilisateur
from django.contrib.auth import get_user_model
# =======================================================================  MUTUALISTES ============================================================================
def mutualiste_listunique(request):
    mutualistes = Mutualisteliste.objects.all().order_by('-mutualiste__numero_contrat', 'type_filiation')
    return render(request, 'backoffice/mutualistes/mutualiste_listuniq.html', {'mutualistes': mutualistes})

# Liste des mutualistes
def mutualiste_list(request):
    mutualistes = Mutualiste.objects.all()
    return render(request, 'backoffice/mutualistes/mutualiste_list.html', {'mutualistes': mutualistes})

def mutualiste_list_actif(request):
    mutualistes = Mutualiste.objects.filter(statut=True)
    return render(request, 'backoffice/mutualistes/mutualiste_list.html', {'mutualistes': mutualistes})

def mutualiste_list_nonactif(request):
    mutualistes = Mutualiste.objects.filter(statut=False)
    return render(request, 'backoffice/mutualistes/mutualiste_list.html', {'mutualistes': mutualistes})

# Création d'un mutualiste avec bénéficiaires
def mutualiste_createok(request):
    if request.method == 'POST':
        mutualiste_form = MutualisteForm(request.POST, request.FILES)
        formset = BeneficiaireFormSet(request.POST)
        if mutualiste_form.is_valid() and formset.is_valid():
            mutualiste = mutualiste_form.save()
            beneficiaries = formset.save(commit=False)
            for beneficiary in beneficiaries:
                beneficiary.mutualiste = mutualiste
                beneficiary.save()
            return redirect('mutualiste_list')
    else:
        mutualiste_form = MutualisteForm()
        formset = BeneficiaireFormSet()
    return render(request, 'backoffice/mutualistes/mutualiste_form.html', {
        'mutualiste_form': mutualiste_form,
        'formset': formset
    })

# Création d'un mutualiste avec bénéficiaires
def mutualiste_createBONAVANTCOTISATION(request):
    if request.method == 'POST':
        mutualiste_form = MutualisteForm(request.POST, request.FILES)
        formset = BeneficiaireFormSet(request.POST)

        if mutualiste_form.is_valid() and formset.is_valid():
            # Création du mutualiste
            mutualiste = mutualiste_form.save()

            # Enregistrement des bénéficiaires
            beneficiaries = formset.save(commit=False)
            for beneficiary in beneficiaries:
                beneficiary.mutualiste = mutualiste
                beneficiary.save()
                
                # Enregistrement dans Mutualisteliste (pour chaque bénéficiaire)
                Mutualisteliste.objects.create(
                    mutualiste=mutualiste,
                    beneficiaire=beneficiary,
                    numero_contrat=mutualiste.numero_contrat,
                    code_matricule=beneficiary.code_matricule,
                    nom=beneficiary.nom,
                    prenom=beneficiary.prenom,
                    date_naissance=beneficiary.date_naissance,
                    sexe=beneficiary.sexe,
                    regime=mutualiste.regime,
                    groupe=mutualiste.groupe,
                    photo=mutualiste.photo,
                    date_adhesion=mutualiste.date_adhesion,
                    statut=mutualiste.statut,
                    observations=mutualiste.observations,
                    type_filiation=beneficiary.type_filiation,
                )

            # Ajouter aussi le mutualiste seul dans Mutualisteliste
            Mutualisteliste.objects.create(
                mutualiste=mutualiste,
                numero_contrat=mutualiste.numero_contrat,
                code_matricule=mutualiste.code_matricule,
                nom=mutualiste.nom,
                prenom=mutualiste.prenom,
                date_naissance=mutualiste.date_naissance,
                sexe=mutualiste.sexe,
                regime=mutualiste.regime,
                groupe=mutualiste.groupe,
                photo=mutualiste.photo,
                date_adhesion=mutualiste.date_adhesion,
                statut=mutualiste.statut,
                observations=mutualiste.observations,
                type_filiation="adherent"
            )

            return redirect('mutualiste_list')

    else:
        mutualiste_form = MutualisteForm()
        formset = BeneficiaireFormSet()

    return render(request, 'backoffice/mutualistes/mutualiste_form.html', {
        'mutualiste_form': mutualiste_form,
        'formset': formset
    })

from django.utils.timezone import now
import calendar

def mutualiste_create(request):
    if request.method == 'POST':
        mutualiste_form = MutualisteForm(request.POST, request.FILES)
        formset = BeneficiaireFormSet(request.POST)

        if mutualiste_form.is_valid() and formset.is_valid():
            # Création du mutualiste
            mutualiste = mutualiste_form.save()
            
            telephone = mutualiste_form.cleaned_data['telephone']
            groupe = mutualiste_form.cleaned_data['groupe']
            utilisateur = get_user_model().objects.create_user(
                username=mutualiste.code_matricule.lower(),  # Utiliser le nom du centre de santé pour le nom d'utilisateur
                #password="P@ssword",  # Vous pouvez définir un mot de passe par défaut ou générer un mot de passe
                password=telephone,
                role='mutualiste',  # Le rôle de l'utilisateur est 'centre_sante' 
                telephone=telephone,
                mutualiste = mutualiste, # Associe l'utilisateur au centre de santé créé
                groupe=groupe,
                last_name=mutualiste.prenom.lower(),
                first_name=mutualiste.nom.lower(),
            )


            # Vérification de l'existence de la cotisation pour le mois en cours
            current_date = now().date()
            mois = current_date.month
            annee = current_date.year
            numero_cotisation = f"{mois:02}{annee}"

            cotisation, created = Cotisation.objects.get_or_create(
                groupe=mutualiste.groupe,
                numero_cotisation=numero_cotisation,
                defaults={
                    'intitule_cotisation': f"{current_date.strftime('%B')} {annee}".capitalize(),
                    'date_debut': f"{annee}-{mois:02}-01",
                    'date_fin': f"{annee}-{mois:02}-{calendar.monthrange(annee, mois)[1]}",
                    'total_adhesion': 0,
                    'total_cotisation': 0,
                    'total_general': 0,
                    'total_payer': 0,
                    'total_restant': 0,
                }
            )

            # Mise à jour des montants de cotisation
            if mutualiste.regime:
                cotisation.total_adhesion += mutualiste.regime.plafond_adhesion or 0
                cotisation.total_cotisation += mutualiste.regime.plafond_cotisation_mensuelle or 0
                cotisation.total_general = cotisation.total_adhesion + cotisation.total_cotisation
                cotisation.save()

            # Enregistrement des bénéficiaires
            beneficiaries = formset.save(commit=False)
            for beneficiary in beneficiaries:
                beneficiary.mutualiste = mutualiste
                beneficiary.save()
                
                # Enregistrement dans Mutualisteliste (pour chaque bénéficiaire)
                Mutualisteliste.objects.create(
                    mutualiste=mutualiste,
                    beneficiaire=beneficiary,
                    numero_contrat=mutualiste.numero_contrat,
                    code_matricule=beneficiary.code_matricule,
                    nom=beneficiary.nom,
                    prenom=beneficiary.prenom,
                    date_naissance=beneficiary.date_naissance,
                    sexe=beneficiary.sexe,
                    regime=mutualiste.regime,
                    groupe=mutualiste.groupe,
                    photo=mutualiste.photo,
                    date_adhesion=mutualiste.date_adhesion,
                    statut=mutualiste.statut,
                    observations=mutualiste.observations,
                    type_filiation=beneficiary.type_filiation,
                )

            # Ajouter aussi le mutualiste seul dans Mutualisteliste
            Mutualisteliste.objects.create(
                mutualiste=mutualiste,
                numero_contrat=mutualiste.numero_contrat,
                code_matricule=mutualiste.code_matricule,
                nom=mutualiste.nom,
                prenom=mutualiste.prenom,
                date_naissance=mutualiste.date_naissance,
                sexe=mutualiste.sexe,
                regime=mutualiste.regime,
                groupe=mutualiste.groupe,
                photo=mutualiste.photo,
                date_adhesion=mutualiste.date_adhesion,
                statut=mutualiste.statut,
                observations=mutualiste.observations,
                type_filiation="adherent"
            )

            return redirect('mutualiste_list')

    else:
        mutualiste_form = MutualisteForm()
        formset = BeneficiaireFormSet()

    return render(request, 'backoffice/mutualistes/mutualiste_form.html', {
        'mutualiste_form': mutualiste_form,
        'formset': formset
    })

  
# Mise à jour d'un mutualiste
def mutualiste_update(request, pk):
    mutualiste = get_object_or_404(Mutualiste, pk=pk)
    if request.method == 'POST':
        mutualiste_form = MutualisteForm(request.POST, request.FILES, instance=mutualiste)
        formset = BeneficiaireFormSet(request.POST, instance=mutualiste)
        if mutualiste_form.is_valid() and formset.is_valid():
            mutualiste = mutualiste_form.save()
            formset.save()
            return redirect('mutualiste_list')
    else:
        mutualiste_form = MutualisteForm(instance=mutualiste)
        formset = BeneficiaireFormSet(instance=mutualiste)
    return render(request, 'backoffice/mutualistes/mutualiste_form.html', {
        'mutualiste_form': mutualiste_form,
        'formset': formset
    })

# Détail d'un mutualiste
def mutualiste_detail(request, pk):
    mutualiste = get_object_or_404(Mutualiste, pk=pk)
    beneficiaires = mutualiste.beneficiaires.all()  # Liste des bénéficiaires liés
    return render(request, 'backoffice/mutualistes/mutualiste_detail.html', {
        'mutualiste': mutualiste,
        'beneficiaires': beneficiaires
    })

# Importations d'un mutualiste
import pandas as pd
import calendar
from django.utils.timezone import now
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import InMemoryUploadedFile

def import_mutualistesAT(request):
    if request.method == 'POST' and request.FILES['file']:
        file = request.FILES['file']
        df = pd.read_excel(file)

        for _, row in df.iterrows():
            try:
                mutualiste = Mutualiste.objects.create(
                    # code_matricule=row['code_matricule'],
                    nom=row['nom'],
                    prenom=row['prenom'],
                    sexe=row['sexe'],
                    date_naissance=row['date_naissance'],
                    telephone=row['telephone'],
                    regime_id=row['regime_id'],
                    groupe_id=row['groupe_id'],
                    # numero_contrat=row['numero_contrat'],
                    date_adhesion=row['date_adhesion'],
                    statut_id=row['statut_id'],
                    observations=row.get('observations', '')
                )

                # Créer un utilisateur lié
                get_user_model().objects.create_user(
                    username=mutualiste.code_matricule.lower(),
                    password=mutualiste.telephone,
                    role='mutualiste',
                    telephone=mutualiste.telephone,
                    mutualiste=mutualiste,
                    groupe=mutualiste.groupe,
                    last_name=mutualiste.prenom.lower(),
                    first_name=mutualiste.nom.lower(),
                )

                # Créer cotisation
                current_date = now().date()
                mois, annee = current_date.month, current_date.year
                numero_cotisation = f"{mois:02}{annee}"

                cotisation, created = Cotisation.objects.get_or_create(
                    groupe=mutualiste.groupe,
                    numero_cotisation=numero_cotisation,
                    defaults={
                        'intitule_cotisation': f"{current_date.strftime('%B')} {annee}".capitalize(),
                        'date_debut': f"{annee}-{mois:02}-01",
                        'date_fin': f"{annee}-{mois:02}-{calendar.monthrange(annee, mois)[1]}",
                        'total_adhesion': 0,
                        'total_cotisation': 0,
                        'total_general': 0,
                        'total_payer': 0,
                        'total_restant': 0,
                    }
                )

                if mutualiste.regime:
                    cotisation.total_adhesion += mutualiste.regime.plafond_adhesion or 0
                    cotisation.total_cotisation += mutualiste.regime.plafond_cotisation_mensuelle or 0
                    cotisation.total_general = cotisation.total_adhesion + cotisation.total_cotisation
                    cotisation.save()

                # Ajouter à Mutualisteliste
                Mutualisteliste.objects.create(
                    mutualiste=mutualiste,
                    numero_contrat=mutualiste.numero_contrat,
                    code_matricule=mutualiste.code_matricule,
                    nom=mutualiste.nom,
                    prenom=mutualiste.prenom,
                    date_naissance=mutualiste.date_naissance,
                    sexe=mutualiste.sexe,
                    regime=mutualiste.regime,
                    groupe=mutualiste.groupe,
                    photo=mutualiste.photo,
                    date_adhesion=mutualiste.date_adhesion,
                    statut=mutualiste.statut,
                    observations=mutualiste.observations,
                    type_filiation="adherent"
                )

            except Exception as e:
                print(f"Erreur lors de l'import du mutualiste {row['nom']}: {e}")
                continue

        return redirect('mutualiste_list')

    return render(request, 'backoffice/mutualistes/import_mutualistes.html')


import pandas as pd
import calendar
from django.utils.timezone import now
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib import messages

from .models import Mutualiste, Mutualisteliste, Regime, Groupe # adapte les imports selon ton projet

def import_mutualistes(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        df = pd.read_excel(file)

        for index, row in df.iterrows():
            try:
                print(f"📥 Ligne {index + 2} : {row.to_dict()}")

                # Récupération des FK
                try:
                    regime = Regime.objects.get(id=int(row['regime_id']))
                    groupe = Groupe.objects.get(id=int(row['groupe_id']))
                except Exception as e:
                    messages.warning(request, f"⚠️ Ligne {index + 2} : Erreur de FK - {e}")
                    continue

                # Création du mutualiste
                mutualiste = Mutualiste.objects.create(
                    # code_matricule=row['code_matricule'],
                    nom=row['nom'],
                    prenom=row['prenom'],
                    sexe=row['sexe'],
                    date_naissance=pd.to_datetime(row['date_naissance']).date(),
                    telephone=str(row['telephone']),
                    regime=regime,
                    groupe=groupe,
                    numero_contrat=row.get('numero_contrat', ''),
                    date_adhesion=pd.to_datetime(row['date_adhesion']).date(),
                    statut=row['statut_id'],
                    observations=row.get('observations', '')
                )

                # Création de l'utilisateur lié
                get_user_model().objects.create_user(
                    username=mutualiste.code_matricule.lower(),
                    password=mutualiste.telephone,
                    role='mutualiste',
                    telephone=mutualiste.telephone,
                    mutualiste=mutualiste,
                    groupe=mutualiste.groupe,
                    last_name=mutualiste.prenom.lower(),
                    first_name=mutualiste.nom.lower(),
                )

                # Création cotisation du mois courant
                current_date = now().date()
                mois, annee = current_date.month, current_date.year
                numero_cotisation = f"{mois:02}{annee}"

                cotisation, created = Cotisation.objects.get_or_create(
                    groupe=mutualiste.groupe,
                    numero_cotisation=numero_cotisation,
                    defaults={
                        'intitule_cotisation': f"{current_date.strftime('%B')} {annee}".capitalize(),
                        'date_debut': f"{annee}-{mois:02}-01",
                        'date_fin': f"{annee}-{mois:02}-{calendar.monthrange(annee, mois)[1]}",
                        'total_adhesion': 0,
                        'total_cotisation': 0,
                        'total_general': 0,
                        'total_payer': 0,
                        'total_restant': 0,
                    }
                )

                if mutualiste.regime:
                    cotisation.total_adhesion += mutualiste.regime.plafond_adhesion or 0
                    cotisation.total_cotisation += mutualiste.regime.plafond_cotisation_mensuelle or 0
                    cotisation.total_general = cotisation.total_adhesion + cotisation.total_cotisation
                    cotisation.save()

                # Ajout à Mutualisteliste
                Mutualisteliste.objects.create(
                    mutualiste=mutualiste,
                    numero_contrat=mutualiste.numero_contrat,
                    code_matricule=mutualiste.code_matricule,
                    nom=mutualiste.nom,
                    prenom=mutualiste.prenom,
                    date_naissance=mutualiste.date_naissance,
                    sexe=mutualiste.sexe,
                    regime=mutualiste.regime,
                    groupe=mutualiste.groupe,
                    photo=mutualiste.photo,  # Assure-toi qu'une photo par défaut existe
                    date_adhesion=mutualiste.date_adhesion,
                    statut=mutualiste.statut,
                    observations=mutualiste.observations,
                    type_filiation="adherent"
                )

                messages.success(request, f"✅ Mutualiste {mutualiste.nom} {mutualiste.prenom} importé avec succès.")

            except Exception as e:
                messages.error(request, f"❌ Ligne {index + 2} : erreur - {e}")
                print(f"Erreur ligne {index + 2} : {e}")
                continue

        return redirect('mutualiste_list')

    return render(request, 'backoffice/mutualistes/import_mutualistes.html')


# ======================================== BENEFICIAIRES =================================================================================================================
# ajouter un ou plusieurs
from django.forms import modelformset_factory
from .forms import BeneficiaireForm

def ajouter_beneficiaires(request, mutualiste_id):
    mutualiste = get_object_or_404(Mutualiste, id=mutualiste_id)
    
    # Création du formset
    BeneficiaireFormSet = modelformset_factory(Beneficiaire, form=BeneficiaireForm, extra=1, can_delete=True)

    if request.method == "POST":
        formset = BeneficiaireFormSet(request.POST, request.FILES, queryset=mutualiste.beneficiaires.all())
        if formset.is_valid():
            beneficiaires = formset.save(commit=False)  # Ne sauvegarde pas encore en base
            for beneficiaire in beneficiaires:
                beneficiaire.mutualiste = mutualiste  # Associe chaque bénéficiaire au mutualiste
                beneficiaire.save()
            return redirect('mutualiste_list')  # Redirige vers la liste des mutualistes
    else:
        formset = BeneficiaireFormSet(queryset=mutualiste.beneficiaires.all())

    return render(request, 'backoffice/mutualistes/ajout_beneficiaires.html', {
        'formset': formset,
        'mutualiste': mutualiste
    })


import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from datetime import datetime

def import_beneficiaires(request):
    if request.method == 'POST' and request.FILES['file']:
        excel_file = request.FILES['file']
        fs = FileSystemStorage()
        filename = fs.save(excel_file.name, excel_file)
        file_path = fs.path(filename)

        try:
            df = pd.read_excel(file_path)

            for _, row in df.iterrows():
                try:
                    mutualiste = Mutualiste.objects.get(id=row['mutualiste_id'])

                    Beneficiaire.objects.create(
                        mutualiste=mutualiste,
                        nom=row['nom'],
                        prenom=row['prenom'],
                        date_naissance=pd.to_datetime(row['date_naissance']).date(),
                        sexe=row['sexe'],
                        type_filiation=row['type_filiation'],
                        telephone=row.get('telephone', None),
                    )
                    
                    # Ajouter à Mutualisteliste
                    Mutualisteliste.objects.create(
                        mutualiste=mutualiste,
                        numero_contrat=mutualiste.numero_contrat,
                        code_matricule=Beneficiaire.code_matricule,
                        nom=Beneficiaire.nom,
                        prenom=Beneficiaire.prenom,
                        date_naissance=Beneficiaire.date_naissance,
                        sexe=Beneficiaire.sexe,
                        regime=mutualiste.regime,
                        groupe=mutualiste.groupe,
                        date_adhesion=mutualiste.date_adhesion,
                        statut=mutualiste.statut,
                        observations=mutualiste.observations,
                        type_filiation=Beneficiaire.type_filiation
                    )
                
                except Mutualiste.DoesNotExist:
                    messages.warning(request, f"Mutualiste ID {row['mutualiste_id']} introuvable.")
                except Exception as e:
                    messages.error(request, f"Erreur pour la ligne {row.to_dict()}: {str(e)}")

            messages.success(request, "Importation des bénéficiaires réussie.")
        except Exception as e:
            messages.error(request, f"Erreur de lecture du fichier: {str(e)}")

        return redirect('beneficiaire_list')  # ou la page de ton choix

    return render(request, 'backoffice/mutualistes/import_beneficiaires.html')


# ======================================================================================================================================================================

from django.contrib import messages
# Activer et désactiver
@csrf_exempt
@login_required
def toggle_mutualiste_status(request, mutualiste_id):
    mutualiste = get_object_or_404(Mutualiste, id=mutualiste_id)
    mutualiste.statut = not mutualiste.statut  # Bascule entre actif et inactif
    mutualiste.save()
    messages.success(request, f"Le statut de {mutualiste.nom} a été mis à jour.")
    return redirect('mutualiste_list')  # Redirige vers la liste des mutualistes


def mutualistes_beneficiaires_list(request):
    mutualistes = Mutualiste.objects.prefetch_related('beneficiaires').all()
    return render(request, 'backoffice/mutualistes/mutualistes_beneficiaires_list.html', {'mutualistes': mutualistes})

# =======================================================================  BENEFICIAIRES ============================================================================
# Liste des beneficiaires
def beneficiaire_list(request):
    beneficiaires = Beneficiaire.objects.all()
    return render(request, 'backoffice/mutualistes/beneficiaire_list.html', {'beneficiaires': beneficiaires})

# ============================= PRESTATIONS SOCIALES =========================================================================================================

# Liste des natures de prestation sociale
def nature_prestation_list(request):
    natures = NaturePrestationSociale.objects.all()
    return render(request, "backoffice/sociale/nature_list.html", {"natures": natures})

# Ajouter une nature de prestation
def nature_prestation_create(request):
    if request.method == "POST":
        form = NaturePrestationSocialeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("nature_list")
    else:
        form = NaturePrestationSocialeForm()
    return render(request, "backoffice/sociale/nature_form.html", {"form": form})

# Modifier une nature de prestation
def nature_prestation_update(request, pk):
    nature = get_object_or_404(NaturePrestationSociale, pk=pk)
    if request.method == "POST":
        form = NaturePrestationSocialeForm(request.POST, instance=nature)
        if form.is_valid():
            form.save()
            return redirect("nature_list")
    else:
        form = NaturePrestationSocialeForm(instance=nature)
    return render(request, "backoffice/sociale/nature_form.html", {"form": form})

# Supprimer une nature de prestation
def nature_prestation_delete(request, pk):
    nature = get_object_or_404(NaturePrestationSociale, pk=pk)
    if request.method == "POST":
        nature.delete()
        return redirect("nature_list")
    return render(request, "backoffice/sociale/nature_confirm_delete.html", {"nature": nature})

# Liste des prestations sociales
def prestation_sociale_list(request):
    prestations = PrestationSociale.objects.all()
    return render(request, "backoffice/sociale/prestation_list.html", {"prestations": prestations})

# Liste des prestations sociales
def prestation_sociale_listsolde(request):
    prestations = PrestationSociale.objects.filter(etat="payé")
    return render(request, "backoffice/sociale/prestation_list.html", {"prestations": prestations})

# Liste des prestations sociales traitées
from django.db.models import Q

def prestation_sociale_listtts(request):
    prestations = PrestationSociale.objects.filter(Q(etat="validé") | Q(etat="rejeté"))
    return render(request, "backoffice/sociale/prestation_list.html", {"prestations": prestations})


# Ajouter une prestation sociale
def prestation_sociale_create(request, pk):
    mutualiste = get_object_or_404(Mutualiste, id=pk)
    if request.method == "POST":
        form = PrestationSocialeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("prestation_sociale_list")
    else:
        form = PrestationSocialeForm(initial={'mutualiste': pk})
    return render(request, "backoffice/sociale/prestation_form.html", {"form": form,"mutualiste":mutualiste})

# Traiter une prestation sociale
def prestation_sociale_traiter(request, pk):
    prestation = get_object_or_404(PrestationSociale, pk=pk)
    mutualiste = prestation.mutualiste
    if request.method == "POST":
        form = PrestationSociale_tts_Form(request.POST, request.FILES, instance=prestation)
        if form.is_valid():
            form.save()
            return redirect("prestation_sociale_list")
    else:
        form = PrestationSociale_tts_Form(instance=prestation)
    return render(request, "backoffice/sociale/prestation_tts_form.html", {"form": form,"mutualiste":mutualiste})

# Modifier une prestation sociale
def prestation_sociale_update(request, pk):
    prestation = get_object_or_404(PrestationSociale, pk=pk)
    if request.method == "POST":
        form = PrestationSocialeForm(request.POST, request.FILES, instance=prestation)
        if form.is_valid():
            form.save()
            return redirect("prestation_sociale_list")
    else:
        form = PrestationSocialeForm(instance=prestation)
    return render(request, "backoffice/sociale/prestation_form.html", {"form": form})

# Supprimer une prestation sociale
def prestation_sociale_delete(request, pk):
    prestation = get_object_or_404(PrestationSociale, pk=pk)
    if request.method == "POST":
        prestation.delete()
        return redirect("prestation_list")
    return render(request, "backoffice/sociale/prestation_confirm_delete.html", {"prestation": prestation})
