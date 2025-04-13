from datetime import datetime, timedelta
import json
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.db.models import Count, Sum
from centres import models
from centres.models import CentreSante
from cotisations.models import Cotisation, MouvementPaiement
from facturations.models import Remboursement
from mutualistes.models import Mutualiste, Mutualisteliste, NaturePrestationSociale, PrestationSociale
from prestations.models import ExamenMedical, Hospitalisation, Medicament, MedicamentUtilise, Prestation, PrestationLunetterie, PrestationPharmacie, PriseEnCharge
from utilisateurs.models import ConnexionUtilisateur, HistoriqueUtilisateur, Utilisateur

def role_required(role):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if hasattr(request.user, 'role') and request.user.role == role:
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("Accès refusé")
        return _wrapped_view
    return decorator

def get_client_ip(request):
    """Récupérer l'adresse IP de l'utilisateur"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            
            # Enregistrer la connexion avec l'adresse IP
            ip_address = get_client_ip(request)
            ConnexionUtilisateur.objects.create(utilisateur=user, adresse_ip=ip_address)
            
            HistoriqueUtilisateur.objects.create(utilisateur=user, action="Connexion réussie")
            
            # Redirection selon le rôle
            if user.is_superuser:
                return redirect('dashboard_superadmin')
            elif user.role == 'administrateur':
                return redirect('tableau_de_bord')
            elif user.role == 'gestionnaire':
                return redirect('tableau_de_bord')
            elif user.role == 'medecin_conseil':
                return redirect('dashboard_medecin')
            elif user.role == 'point_focal':
                return redirect('dashboard_point_focal')
            elif user.role == 'centre_sante':
                return redirect('dashboard_centre_sante')
            elif user.role == 'pharmacie':
                return redirect('tableau_de_bord_pharmacie')
            elif user.role == 'lunetterie':
                return redirect('dashboard_optique')
            else:
                messages.error(request, "Rôle non défini")
                return redirect('login')
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect")
    return render(request, 'frontoffice/authentification/login.html')


# @login_required
# def logout_view(request):
#     logout(request)
#     return redirect('login')

@login_required
def logout_view(request):
    user = request.user
    if user.is_authenticated:
        # Ajouter l'historique de déconnexion
        HistoriqueUtilisateur.objects.create(utilisateur=user, action="Déconnexion")

    logout(request)
    return redirect('login')


def tableau_de_bord(request):
    utilisateur = request.user
    contexte = {}



    return render(request, 'dashboard/tableau_de_bord.html', contexte)



@login_required
def tableau_de_bord1(request):
    """
    Vue principale pour afficher le tableau de bord des utilisateurs selon leurs rôles.
    """
    utilisateur = request.user
    contexte = {}

    if utilisateur.role == 'SUPER_ADMIN':
        # Affiche toutes les fonctionnalités disponibles
        contexte['actions'] = {
            'Gestion des utilisateurs': '/admin/utilisateurs/',
            'Gestion des mutualistes': '/admin/mutualistes/',
            'Gestion des centres de santé': '/admin/centres_sante/',
            'Historique des actions': '/admin/historique/',
        }
        contexte['stats'] = {
            'Total des mutualistes': Mutualiste.objects.count(),
            'Total des centres de santé': CentreSante.objects.count(),
            
        }

    elif utilisateur.role == 'ADMIN':
        # Gestion des utilisateurs (sauf super administrateurs)
        contexte['actions'] = {
            'Créer un utilisateur': '/admin/utilisateurs/add/',
            'Voir les utilisateurs': '/admin/utilisateurs/',
        }

    elif utilisateur.role == 'MEDECIN_CONSEIL':
        # Valider les prestations médicales
        prestations_soumises = HistoriqueUtilisateur.objects.filter(action="Prestation soumise").count()
        contexte['actions'] = {
            'Valider prestations': '/medecin/prestations_a_valider/',
            'Recommandations médicales': '/medecin/recommandations/',
        }
        contexte['stats'] = {
            'Prestations en attente de validation': prestations_soumises,
        }

    elif utilisateur.role == 'POINT_FOCAL':
        # Accès aux informations du groupe
        groupe = utilisateur.groupe
        mutualistes = Mutualiste.objects.filter(groupe=groupe).count()
        contexte['actions'] = {
            'Voir les mutualistes': f'/point_focal/mutualistes/{groupe.id}/',
            'Renouveler une ordonnance': '/point_focal/ordonnances_renouvelables/',
        }
        contexte['stats'] = {
            'Nombre de mutualistes dans votre groupe': mutualistes,
        }

    elif utilisateur.role == 'CENTRE_SANTE':
        # Prestations pour ce centre
        prestations_centre = HistoriqueUtilisateur.objects.filter(utilisateur=utilisateur).count()
        contexte['actions'] = {
            'Voir les prestations': '/centre_sante/prestations/',
        }
        contexte['stats'] = {
            'Prestations fournies': prestations_centre,
        }

    elif utilisateur.role == 'PHARMACIE':
        # Prestations pharmaceutiques
        prescriptions_servies = HistoriqueUtilisateur.objects.filter(action="Prescription servie").count()
        contexte['actions'] = {
            'Voir les prestations pharmaceutiques': '/pharmacie/prestations/',
        }
        contexte['stats'] = {
            'Prescriptions servies': prescriptions_servies,
        }

    return render(request, 'tableau_de_bord.html', contexte)


from django.db.models import Sum, Count

from django.shortcuts import render
from django.db.models import Count, Sum, Q
from django.utils.timezone import now

def tableau_de_bord(request):
    # Récupération de la date actuelle
    date_actuelle = now()
    annee_courante = date_actuelle.year
    mois_courant = date_actuelle.month

    # Indicateurs clés
    total_mutualistes = Mutualiste.objects.count()
    nouveaux_mutualistes = Mutualiste.objects.filter(date_adhesion__year=annee_courante, date_adhesion__month=mois_courant).count()

    total_prestations = PrestationPharmacie.objects.count()
    prestations_mois = PrestationPharmacie.objects.filter(date_prestation__year=annee_courante, date_prestation__month=mois_courant).count()

    total_montant_prestations = PrestationPharmacie.objects.aggregate(Sum('montant_total'))['montant_total__sum'] or 0

    total_medicaments = Medicament.objects.count()
    
    total_centres = CentreSante.objects.count()
    centres_actifs = CentreSante.objects.annotate(n_prestations=Count('prestations_pharmacie')).order_by('-n_prestations')[:5]

    total_utilisateurs = Utilisateur.objects.count()

    
    total_demandes = PriseEnCharge.objects.filter().count()
    demandes_valide = Prestation.objects.filter(statut_validation=True).count()
    demandes_en_attente = Prestation.objects.filter(statut_validation=False).count()
    total_prestations = Prestation.objects.filter().count()

    # Contexte à passer au template
    context = {
        'total_mutualistes': total_mutualistes,
        'nouveaux_mutualistes': nouveaux_mutualistes,
        'total_prestations': total_prestations,
        'prestations_mois': prestations_mois,
        'total_montant_prestations': total_montant_prestations,
        'total_medicaments': total_medicaments,
        'total_centres': total_centres,
        'centres_actifs': centres_actifs,
        'total_utilisateurs': total_utilisateurs,
        'total_demandes': total_demandes,
        'demandes_en_attente': demandes_en_attente,
        'demandes_valide': demandes_valide,
    }

    return render(request, "dashboard/dashboard_admin.html", context)



# centre_sante_dashboard_view ======================================================================================================================================
def centre_sante_dashboard_view1(request):
    centre_sante = request.user.centre_sante

    # Statistiques globales
    total_prises_en_charge = PriseEnCharge.objects.filter(centre=centre_sante).count()
    total_prestationsvalide = Prestation.objects.filter(centre_sante=centre_sante, statut_validation=True).count()
    total_prestationsnonvalide = Prestation.objects.filter(centre_sante=centre_sante, statut_validation=False).count()
    total_prestations = Prestation.objects.filter(centre_sante=centre_sante).count()
    montant_total_prestations = Prestation.objects.filter(
        centre_sante=centre_sante, 
        statut_validation=True
    ).aggregate(Sum('montant_total'))['montant_total__sum'] or 0

    # Évolution des prises en charge par mois
    prises_par_mois = (
        PriseEnCharge.objects
        .filter(centre=centre_sante)
        .values('date_prise_en_charge__year', 'date_prise_en_charge__month')
        .annotate(total=Count('id'))
        .order_by('date_prise_en_charge__year', 'date_prise_en_charge__month')
    )

    # Évolution des prestations par mois
    prestations_par_mois = (
        Prestation.objects
        .filter(centre_sante=centre_sante)
        .values('date_prestation__year', 'date_prestation__month')
        .annotate(total=Count('id'))
        .order_by('date_prestation__year', 'date_prestation__month')
    )

    # Formatage des données pour Chart.js
    prises_labels = [f"{item['date_prise_en_charge__year']}-{item['date_prise_en_charge__month']:02d}" for item in prises_par_mois]
    prises_values = [item['total'] for item in prises_par_mois]

    prestations_labels = [f"{item['date_prestation__year']}-{item['date_prestation__month']:02d}" for item in prestations_par_mois]
    prestations_values = [item['total'] for item in prestations_par_mois]

    context = {
        "total_prises_en_charge": total_prises_en_charge,
        "total_prestations": total_prestations,
        "total_prestationsvalide": total_prestationsvalide,
        "total_prestationsnonvalide": total_prestationsnonvalide,
        "montant_total_prestations": montant_total_prestations,
        "prises_labels": json.dumps(prises_labels),
        "prises_values": json.dumps(prises_values),
        "prestations_labels": json.dumps(prestations_labels),
        "prestations_values": json.dumps(prestations_values),
    }

    return render(request, 'dashboard/centre_sante_dashboard.html', context)


def centre_sante_dashboard_view(request):
    centre_sante = request.user.centre_sante

    # Statistiques globales
    total_prises_en_charge = PriseEnCharge.objects.filter(centre=centre_sante).count()
    total_prestationsvalide = Prestation.objects.filter(centre_sante=centre_sante, statut_validation=True).count()
    total_prestationsnonvalide = Prestation.objects.filter(centre_sante=centre_sante, statut_validation=False).count()
    total_prestations = Prestation.objects.filter(centre_sante=centre_sante).count()
    montant_total_prestations = Prestation.objects.filter(
        centre_sante=centre_sante, 
        statut_validation=True
    ).aggregate(Sum('montant_total'))['montant_total__sum'] or 0
    # messageprestation = Prestation.objects.filter(centre_sante=centre_sante, date_validation__isnull=False).order_by('-date_validation')[:5]
    messageprestation = Prestation.objects.filter(
        centre_sante=centre_sante, 
        date_validation__isnull=False
    ).exclude(
        prestation__categorie__in=["consultation", "visite"]
    ).order_by('-date_validation')[:5]


    # Évolution des prises en charge par mois
    prises_par_mois = (
        PriseEnCharge.objects
        .filter(centre=centre_sante)
        .values('date_prise_en_charge__year', 'date_prise_en_charge__month')
        .annotate(total=Count('id'))
        .order_by('date_prise_en_charge__year', 'date_prise_en_charge__month')
    )

    # Évolution des prestations par mois
    prestations_par_mois = (
        Prestation.objects
        .filter(centre_sante=centre_sante)
        .values('date_prestation__year', 'date_prestation__month')
        .annotate(total=Count('id'))
        .order_by('date_prestation__year', 'date_prestation__month')
    )

    # ✅ Correction : Gérer les valeurs None en remplaçant par 0
    prises_labels = [
        f"{item['date_prise_en_charge__year']}-{(item['date_prise_en_charge__month'] or 0):02d}"
        for item in prises_par_mois
    ]
    prises_values = [item['total'] for item in prises_par_mois]

    prestations_labels = [
        f"{item['date_prestation__year']}-{(item['date_prestation__month'] or 0):02d}"
        for item in prestations_par_mois
    ]
    prestations_values = [item['total'] for item in prestations_par_mois]

    context = {
        "total_prises_en_charge": total_prises_en_charge,
        "total_prestations": total_prestations,
        "total_prestationsvalide": total_prestationsvalide,
        "total_prestationsnonvalide": total_prestationsnonvalide,
        "montant_total_prestations": montant_total_prestations,
        "prises_labels": json.dumps(prises_labels),
        "prises_values": json.dumps(prises_values),
        "prestations_labels": json.dumps(prestations_labels),
        "prestations_values": json.dumps(prestations_values),
        "messageprestation" :messageprestation 
    }

    return render(request, 'dashboard/centre_sante_dashboard.html', context) 


def optique_dashboard_view(request):
    centre_sante = request.user.centre_sante

    # Statistiques globales
    total_prises_en_charge = PriseEnCharge.objects.filter(centre=centre_sante).count()
    total_prestationsvalide = Prestation.objects.filter(centre_sante=centre_sante, statut_validation=True).count()
    total_prestationsnonvalide = Prestation.objects.filter(centre_sante=centre_sante, statut_validation=False).count()
    total_prestations = Prestation.objects.filter(centre_sante=centre_sante).count()
    montant_total_prestations = Prestation.objects.filter(
        centre_sante=centre_sante, 
        statut_validation=True
    ).aggregate(Sum('montant_total'))['montant_total__sum'] or 0
    # messageprestation = Prestation.objects.filter(centre_sante=centre_sante, date_validation__isnull=False).order_by('-date_validation')[:5]
    messageprestation = Prestation.objects.filter(
        centre_sante=centre_sante, 
        date_validation__isnull=False
    ).exclude(
        prestation__categorie__in=["consultation", "visite"]
    ).order_by('-date_validation')[:5]
    
    # Évolution des prises en charge par mois
    prises_par_mois = (
        PriseEnCharge.objects
        .filter(centre=centre_sante)
        .values('date_prise_en_charge__year', 'date_prise_en_charge__month')
        .annotate(total=Count('id'))
        .order_by('date_prise_en_charge__year', 'date_prise_en_charge__month')
    )

    # Évolution des prestations par mois
    prestations_par_mois = (
        Prestation.objects
        .filter(centre_sante=centre_sante)
        .values('date_prestation__year', 'date_prestation__month')
        .annotate(total=Count('id'))
        .order_by('date_prestation__year', 'date_prestation__month')
    )

    # ✅ Correction : Gérer les valeurs None en remplaçant par 0
    prises_labels = [
        f"{item['date_prise_en_charge__year']}-{(item['date_prise_en_charge__month'] or 0):02d}"
        for item in prises_par_mois
    ]
    prises_values = [item['total'] for item in prises_par_mois]

    prestations_labels = [
        f"{item['date_prestation__year']}-{(item['date_prestation__month'] or 0):02d}"
        for item in prestations_par_mois
    ]
    prestations_values = [item['total'] for item in prestations_par_mois] 

    context = {
        "total_prises_en_charge": total_prises_en_charge,
        "total_prestations": total_prestations,
        "total_prestationsvalide": total_prestationsvalide,
        "total_prestationsnonvalide": total_prestationsnonvalide,
        "montant_total_prestations": montant_total_prestations,
        "prises_labels": json.dumps(prises_labels),
        "prises_values": json.dumps(prises_values),
        "prestations_labels": json.dumps(prestations_labels),
        "prestations_values": json.dumps(prestations_values),
        "messageprestation" :messageprestation 
    }

    return render(request, 'dashboard/optique_dashboard.html', context)

# TABLEAU DE BORD PAR CALENDRIER ======================================================================================================================================
def get_prise_en_charge_events(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Utilisateur non authentifié"}, status=401)

    if not hasattr(request.user, 'centre_sante'):
        return JsonResponse({"error": "Aucun centre de santé associé à cet utilisateur"}, status=403)

    # Récupérer les prises en charge du centre de santé de l'utilisateur
    prises = PriseEnCharge.objects.filter(centre=request.user.centre_sante)

    # Affichage des prises en charge trouvées dans la console du serveur
    print(f"Prises en charge trouvées ({len(prises)}):")
    for prise in prises:
        print(f"- {prise.numero_dossier} | Date: {prise.date_prise_en_charge} | Centre: {prise.centre.nom}")

    # Construire la liste des événements pour le calendrier
    events = [
        {
            "title": f"PEC {prise.numero_dossier}",
            "start": prise.date_prise_en_charge.strftime('%Y-%m-%d'),
            "color": "#007bff",
        }
        for prise in prises
    ]

    return JsonResponse(events, safe=False)

# TABLEAU DE BORD PHARMACIE ======================================================================================================================================
def tableau_de_bord_pharmacie(request):
    centre_sante = request.user.centre_sante
    aujourd_hui = datetime.now()
    debut_mois = aujourd_hui.replace(day=1)
    debut_semaine = aujourd_hui - timedelta(days=aujourd_hui.weekday())

    prestations = PrestationPharmacie.objects.filter(centre_sante=centre_sante)

    context = {
        "total_prestations": prestations.count(),
        "montant_total": prestations.aggregate(Sum('montant_total'))['montant_total__sum'] or 0,
        "part_mutualiste": prestations.aggregate(Sum('part_mutualiste'))['part_mutualiste__sum'] or 0,
        "part_mutuelle": prestations.aggregate(Sum('part_mutuelle'))['part_mutuelle__sum'] or 0,
        "prestations_par_mois": prestations.filter(date_prestation__gte=debut_mois).count(),
        "prestations_par_semaine": prestations.filter(date_prestation__gte=debut_semaine).count(),
        "medicaments_plus_prescrits": list(MedicamentUtilise.objects.filter(
            prestation_pharmacie__centre_sante=centre_sante
        ).values('medicament__nom').annotate(
            total_vendu=Sum('quantite_servie')
        ).order_by('-total_vendu')[:5])
    }

    return render(request, 'dashboard/tableau_de_bord_pharmacie.html', context)

# TABLEAU DE BORD CONSEIL ======================================================================================================================================
def dashboard_medecinok(request):
    stats = {
        "hospitalisations_en_attente": Hospitalisation.objects.filter(statut_prise_en_charge="en_attente").count(),
        "hospitalisations_validees": Hospitalisation.objects.filter(statut_prise_en_charge="validee").count(),
        "hospitalisations_refusees": Hospitalisation.objects.filter(statut_prise_en_charge="refusee").count(),
        
        "examens_en_attente": ExamenMedical.objects.filter(statut="en_attente").count(),
        "examens_valides": ExamenMedical.objects.filter(statut="validee").count(),
        "examens_refuses": ExamenMedical.objects.filter(statut="refusee").count(), 
        
        "optiques_en_attente": PrestationLunetterie.objects.filter(statut="en_attente").count(),
        "optiques_valides": PrestationLunetterie.objects.filter(statut="validee").count(),
        "optiques_refuses": PrestationLunetterie.objects.filter(statut="refusee").count(),  
    }

    return render(request, 'dashboard/dashboard_medecin.html', {"stats": stats})

from datetime import datetime, timedelta
from django.utils.timezone import now

def dashboard_medecin(request):
    periode = request.GET.get("periode", "mois")
    today = now()
    
    if periode == "jour":
        date_limit = today - timedelta(days=1)
    elif periode == "semaine":
        date_limit = today - timedelta(days=7)
    elif periode == "annee":
        date_limit = today - timedelta(days=365)
    else:  # par défaut mois
        date_limit = today - timedelta(days=30)

    stats = {
        "hospitalisations_en_attente": Hospitalisation.objects.filter(statut_prise_en_charge="en_attente", date_admission__gte=date_limit).count(),
        "hospitalisations_validees": Hospitalisation.objects.filter(statut_prise_en_charge="validee", date_admission__gte=date_limit).count(),
        "hospitalisations_refusees": Hospitalisation.objects.filter(statut_prise_en_charge="refusee", date_admission__gte=date_limit).count(),

        "examens_en_attente": ExamenMedical.objects.filter(statut="en_attente", date_prescription__gte=date_limit).count(),
        "examens_valides": ExamenMedical.objects.filter(statut="validee", date_prescription__gte=date_limit).count(),
        "examens_refuses": ExamenMedical.objects.filter(statut="refusee", date_prescription__gte=date_limit).count(),

        "optiques_en_attente": PrestationLunetterie.objects.filter(statut="en_attente", date_prestation__gte=date_limit).count(),
        "optiques_valides": PrestationLunetterie.objects.filter(statut="validee", date_prestation__gte=date_limit).count(),
        "optiques_refuses": PrestationLunetterie.objects.filter(statut="refusee", date_prestation__gte=date_limit).count(),
    }

    return render(request, 'dashboard/dashboard_medecin.html', {"stats": stats, "periode": periode})


# TABLEAU DE BORD POINT FOCAL ======================================================================================================================================

@login_required
def dashboard_point_focal(request):
    utilisateur = request.user
    groupe = utilisateur.groupe

    # Récupérer les mutualistes et prestations du groupe
    mutualistes = Mutualiste.objects.filter(groupe=groupe)
    prestations = Prestation.objects.filter(centre_sante__groupe=groupe)

    # Statistiques générales
    total_mutualistes = mutualistes.count()
    total_prestations = prestations.count()
    total_prestations_montant = prestations.aggregate(Sum('montant_total'))['montant_total__sum'] or 0
    
    # Comptage des centres de santé selon leur type
    centres = CentreSante.objects.filter(groupe=groupe)
    nombre_pharmacies = centres.filter(type="Pharmacie").count()
    nombre_lunetteries = centres.filter(type="Lunetterie").count()
    nombre_autres = centres.exclude(type__in=["Pharmacie", "Lunetterie"]).count()

    context = {
        'utilisateur': utilisateur,
        'groupe': groupe,
        'mutualistes': mutualistes,
        'prestations': prestations,
        'total_mutualistes': total_mutualistes,
        'total_prestations': total_prestations,
        'total_prestations_montant': total_prestations_montant,
        'nombre_pharmacies': nombre_pharmacies,
        'nombre_lunetteries': nombre_lunetteries,
        'nombre_autres': nombre_autres,
    }
    return render(request, 'dashboard/dashboard_point_focal.html', context)


@login_required
def point_focal(request):
    utilisateur = request.user
    groupe = utilisateur.groupe

    # Récupérer les mutualistes et prestations du groupe
    mutualistes = Mutualiste.objects.filter(groupe=groupe)
    prestations = Prestation.objects.filter(centre_sante__groupe=groupe)
    
    context = {
            'utilisateur': utilisateur,
            'groupe': groupe,
            'mutualistes': mutualistes,
            'prestations': prestations,
        }
    return render(request, 'dashboard/listemutualistegroupe.html', context)

@login_required
def point_focal_mutualiste(request):
    utilisateur = request.user
    groupe = utilisateur.groupe

    # Récupérer les mutualistes et prestations du groupe
    mutualistes = Mutualisteliste.objects.filter(groupe=groupe).order_by('-mutualiste__numero_contrat')
    #mutualistes = Mutualiste.objects.filter(groupe=groupe)
    prestations = Prestation.objects.filter(centre_sante__groupe=groupe)
    
    context = {
            'utilisateur': utilisateur,
            'groupe': groupe,
            'mutualistes': mutualistes, 
            'prestations': prestations,
        }
    return render(request, 'dashboard/pointfocal/point_focal_mutualiste.html', context) 

@login_required
def point_focal_prestataire(request):
    utilisateur = request.user
    groupe = utilisateur.groupe

    # Récupérer les mutualistes et prestations du groupe
    mutualistes = Mutualisteliste.objects.filter(groupe=groupe).order_by('-mutualiste__numero_contrat', '-mutualiste__type_filiation')
    #mutualistes = Mutualiste.objects.filter(groupe=groupe)
    prestations = Prestation.objects.filter(centre_sante__groupe=groupe)
    centres = CentreSante.objects.filter(groupe=groupe)
    context = {
            'utilisateur': utilisateur,
            'groupe': groupe,
            'mutualistes': mutualistes,
            'prestations': prestations,
            'centres' : centres
        }
    return render(request, 'dashboard/pointfocal/point_focal_prestataire.html', context)

@login_required
def point_focal_prestations(request):
    utilisateur = request.user
    groupe = utilisateur.groupe

    # Récupérer les mutualistes et prestations du groupe
    mutualistes = Mutualisteliste.objects.filter(groupe=groupe).order_by('-mutualiste__numero_contrat', '-mutualiste__type_filiation')
    #mutualistes = Mutualiste.objects.filter(groupe=groupe)
    prestations = Prestation.objects.filter(centre_sante__groupe=groupe).order_by('-date_prestation')
    centres = CentreSante.objects.filter(groupe=groupe)
    context = {
            'utilisateur': utilisateur,
            'groupe': groupe,
            'mutualistes': mutualistes,
            'prestations': prestations,
            'centres' : centres
        }
    return render(request, 'dashboard/pointfocal/point_focal_prestation.html', context)

@login_required
def point_focal_dispensations(request):
    utilisateur = request.user
    groupe = utilisateur.groupe

    # Récupérer les mutualistes et prestations du groupe
    mutualistes = Mutualisteliste.objects.filter(groupe=groupe).order_by('-mutualiste__numero_contrat', '-mutualiste__type_filiation')
    #mutualistes = Mutualiste.objects.filter(groupe=groupe)
    prestations = Prestation.objects.filter(centre_sante__groupe=groupe).order_by('-date_prestation')
    dispensations = PrestationPharmacie.objects.filter(centre_sante__groupe=groupe).order_by('-date_prestation')
    centres = CentreSante.objects.filter(groupe=groupe)
    context = {
            'utilisateur': utilisateur,
            'groupe': groupe,
            'mutualistes': mutualistes,
            'prestations': prestations,
            'centres' : centres,
            'dispensations' : dispensations
        }
    return render(request, 'dashboard/pointfocal/point_focal_dispensation.html', context)

@login_required
def point_focal_cotisations(request):
    utilisateur = request.user
    groupe = utilisateur.groupe
    cotisations = Cotisation.objects.filter(groupe=groupe)
    return render(request, 'dashboard/pointfocal/liste_cotisations.html', {'cotisations': cotisations})

@login_required
def point_focal_paiements(request, cotisation_id):
    utilisateur = request.user
    groupe = utilisateur.groupe
    paiements = MouvementPaiement.objects.filter(cotisation=cotisation_id,cotisation__groupe=groupe)
    return render(request, 'dashboard/pointfocal/liste_paiements.html', {'paiements': paiements})

# ================================== CATEGORIES =============
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import CategorieAffection
from .forms import CategorieAffectionForm

# 📌 Lister toutes les catégories d'affection
def liste_categories(request):
    categories = CategorieAffection.objects.all().order_by('nom')
    return render(request, 'backoffice/categorie_affection/liste.html', {'categories': categories})

# 📌 Ajouter une catégorie
def ajouter_categorie(request):
    if request.method == "POST":
        form = CategorieAffectionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Catégorie ajoutée avec succès.")
            return redirect('categorie_liste')
    else:
        form = CategorieAffectionForm()
    return render(request, 'backoffice/categorie_affection/formulaire.html', {'form': form})

# 📌 Modifier une catégorie
def modifier_categorie(request, pk):
    categorie = get_object_or_404(CategorieAffection, pk=pk)
    if request.method == "POST":
        form = CategorieAffectionForm(request.POST, instance=categorie)
        if form.is_valid():
            form.save()
            messages.success(request, "Catégorie mise à jour avec succès.")
            return redirect('categorie_liste')
    else:
        form = CategorieAffectionForm(instance=categorie)
    return render(request, 'backoffice/categorie_affection/formulaire.html', {'form': form})

# 📌 Supprimer une catégorie
def supprimer_categorie(request, pk): 
    categorie = get_object_or_404(CategorieAffection, pk=pk)
    if request.method == "POST":
        categorie.delete()
        messages.success(request, "Catégorie supprimée avec succès.")
        return redirect('categorie_liste')
    return render(request, 'backoffice/categorie_affection/confirmation_suppression.html', {'categorie': categorie})


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import CodeAffection, Ordonnance
from .forms import CodeAffectionForm, OrdonnanceForm

# Liste des codes d'affection
def code_affection_list(request):
    codes = CodeAffection.objects.all()
    return render(request, 'backoffice/code_affection/list.html', {'codes': codes})

# Ajouter un code d'affection
def code_affection_create(request):
    if request.method == 'POST':
        form = CodeAffectionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Code d'affection ajouté avec succès !")
            return redirect('code_affection_list')
    else:
        form = CodeAffectionForm()
    return render(request, 'backoffice/code_affection/form.html', {'form': form})

# Modifier un code d'affection
def code_affection_update(request, pk):
    code = get_object_or_404(CodeAffection, pk=pk)
    if request.method == 'POST':
        form = CodeAffectionForm(request.POST, instance=code)
        if form.is_valid():
            form.save()
            messages.success(request, "Code d'affection modifié avec succès !")
            return redirect('code_affection_list')
    else:
        form = CodeAffectionForm(instance=code)
    return render(request, 'backoffice/code_affection/form.html', {'form': form})

# Supprimer un code d'affection
def code_affection_delete(request, pk):
    code = get_object_or_404(CodeAffection, pk=pk)
    if request.method == 'POST':
        code.delete()
        messages.success(request, "Code d'affection supprimé avec succès !")
        return redirect('code_affection_list')
    return render(request, 'backoffice/code_affection/confirm_delete.html', {'code': code})

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Ordonnance
from .forms import OrdonnanceForm

# Liste des ordonnances
def ordonnance_list(request):
    ordonnances = Ordonnance.objects.all().order_by('-date_emission')
    return render(request, 'backoffice/ordonnance/list.html', {'ordonnances': ordonnances})

# Ajouter une ordonnance
def ordonnance_create(request):
    if request.method == 'POST':
        form = OrdonnanceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Ordonnance ajoutée avec succès !")
            return redirect('ordonnance_list')
    else:
        form = OrdonnanceForm()
    return render(request, 'backoffice/ordonnance/form.html', {'form': form})

# Modifier une ordonnance
def ordonnance_update(request, pk):
    ordonnance = get_object_or_404(Ordonnance, pk=pk)
    if request.method == 'POST':
        form = OrdonnanceForm(request.POST, instance=ordonnance)
        if form.is_valid():
            form.save()
            messages.success(request, "Ordonnance modifiée avec succès !")
            return redirect('ordonnance_list')
    else:
        form = OrdonnanceForm(instance=ordonnance)
    return render(request, 'backoffice/ordonnance/form.html', {'form': form})

# Supprimer une ordonnance
def ordonnance_delete(request, pk):
    ordonnance = get_object_or_404(Ordonnance, pk=pk)
    if request.method == 'POST':
        ordonnance.delete()
        messages.success(request, "Ordonnance supprimée avec succès !")
        return redirect('ordonnance_list')
    return render(request, 'backoffice/ordonnance/confirm_delete.html', {'ordonnance': ordonnance})














# ================================== API ============================================================ API ==================================================
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate, login
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.authtoken.models import Token
from django.utils import timezone
import logging
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework import status, permissions
from rest_framework_simplejwt.views import TokenRefreshView

User = get_user_model()

class LoginView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # Mettre à jour le champ last_login
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        # Générer ou récupérer le token
        token, created = Token.objects.get_or_create(user=user)

        # Générer un **nouveau token JWT** (Access + Refresh)
        refresh = RefreshToken.for_user(user)

        print(f"✅ Nouveau token généré pour {user.username}: {str(refresh.access_token)}")
        
        # Vérifier si le token est bien généré
        print(f"✅ Token généré pour {user.username}: {token.key}")

        return Response({
            'token': token.key,  # Vérifier ici si la clé est bien présente
            'refresh': str(token),
            'role': getattr(user, 'role', None),
            'last_login': user.last_login,
            'email': user.email,
            'user_id': user.pk,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'photo': user.photo.url if hasattr(user, "photo") and user.photo else None,
        }, status=status.HTTP_200_OK)

class RefreshTokenView(TokenRefreshView):
    """Vue pour rafraîchir un token JWT expiré"""
    pass  # Utilise la classe existante de DRF




# Vue pour deconnection
# @csrf_exempt
def logout_userbank(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

class RegisterView(APIView):
    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")

        if Utilisateur.objects.filter(username=username).exists():
            return Response({"error": "Username already taken"}, status=status.HTTP_400_BAD_REQUEST)

        user = Utilisateur.objects.create_user(username=username, email=email, password=password)
        return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
        })

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def secure_endpoint(request):
    return Response({"message": "You have access to this secure data"})


# ========================================== Liste du reseaux ==========================================================================================================
from rest_framework import generics # type: ignore
from .serializers import CentreSanteSerializer, NaturePrestationSocialeSerializer, PrestationPharmacieSerializer, PrestationSerializer, PrestationSocialeSerializer, RemboursementSerializer

class CentreSanteListCreateView(generics.ListCreateAPIView):
    queryset = CentreSante.objects.filter(type="hopital")
    serializer_class = CentreSanteSerializer

    def get(self, request, *args, **kwargs):
        auth_header = request.headers.get('Authorization')
        print(f"🔍 Token reçu par l'API: {auth_header}")
        return super().get(request, *args, **kwargs)

from rest_framework import generics
from rest_framework.permissions import AllowAny  # Autorise tout le monde
from .serializers import CentreSanteSerializer

class HopitalListView(generics.ListAPIView):
    """
    Vue pour récupérer la liste des hôpitaux actifs sans authentification.
    """
    queryset = CentreSante.objects.filter(statut=True) 
    serializer_class = CentreSanteSerializer
    permission_classes = [AllowAny]  # Cette ligne permet à tout le monde d'accéder à cette vue, sans authentification
    
class HopitalListViewcro(generics.ListAPIView):
    """
    Vue pour récupérer la liste des hôpitaux actifs sans authentification.
    """
    queryset = CentreSante.objects.exclude(type="pharmacie").filter(statut=True) 
    serializer_class = CentreSanteSerializer
    permission_classes = [AllowAny]  # Cette ligne permet à tout le monde d'accéder à cette vue, sans authentification

class PharmacieListView(generics.ListAPIView):
    """
    Vue pour récupérer la liste des hôpitaux actifs sans authentification.
    """
    queryset = CentreSante.objects.filter(type="pharmacie", statut=True)
    serializer_class = CentreSanteSerializer
    permission_classes = [AllowAny]  # Cette ligne permet à tout le monde d'accéder à cette vue, sans authentification


# ================================================ INFORMATIONS CODE ================================================================
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .models import Mutualiste
from .serializers import MutualisteSerializer

class ProfilMutualisteView(APIView):
    """
    Vue pour récupérer les informations du mutualiste connecté et ses bénéficiaires.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            mutualiste = request.user.mutualiste  # On suppose que `Mutualiste` est lié à `User`
            data = MutualisteSerializer(mutualiste).data
            return Response(data, status=200)
        except Mutualiste.DoesNotExist:
            return Response({"error": "Mutualiste non trouvé"}, status=404)

# =========================================================================================== 
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import PrestationSerializer, PrestationPharmacieSerializer
from rest_framework.permissions import IsAuthenticated

class PrestationCombinedViewSet(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Récupérer le mutualiste connecté
        mutualiste = request.user.mutualiste  

        # Récupérer les prestations classiques (via prise_en_charge)
        prestations_classiques = Prestation.objects.filter(prise_en_charge__mutualiste=mutualiste)

        # Récupérer les prestations pharmacie (via prise_en_charge)
        prestations_pharmacie = PrestationPharmacie.objects.filter(mutualiste=mutualiste)

        # Sérialiser les données
        prestations_classiques_serializer = PrestationSerializer(prestations_classiques, many=True)
        prestations_pharmacie_serializer = PrestationPharmacieSerializer(prestations_pharmacie, many=True)

        print(prestations_classiques_serializer.data)
        print(prestations_pharmacie_serializer.data)
        # Retourner la réponse
        return Response({
            "prestations_classiques": prestations_classiques_serializer.data,
            "prestations_pharmacie": prestations_pharmacie_serializer.data,
        }, status=status.HTTP_200_OK)

#=========================================  Demande remboursement ============================================================================
from rest_framework import generics
from rest_framework.parsers import MultiPartParser, FormParser

class RemboursementListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    queryset = Remboursement.objects.all().order_by('-date_remboursement')
    serializer_class = RemboursementSerializer
    parser_classes = (MultiPartParser, FormParser)

    def perform_create(self, serializer):
        # Associer le remboursement à l'utilisateur connecté
        serializer.save(mutualiste=self.request.user.mutualiste)

#============== Sociale ========================================================================================================================================
class PrestationSocialeListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]  # Permet uniquement aux utilisateurs authentifiés d'accéder à cette vue

    queryset = PrestationSociale.objects.all().order_by('-date_soumission')
    serializer_class = PrestationSocialeSerializer
    parser_classes = (MultiPartParser, FormParser)  # Permet de gérer les fichiers multipart

    def perform_create(self, serializer):
        # Associer la prestation sociale au mutualiste (utilisateur connecté)
        mutualiste = self.request.user.mutualiste
        prestation_sociale = serializer.save(mutualiste=mutualiste)
        
        # Affichage des données sérialisées
        print(f"Prestation Sociale sérialisée: {PrestationSocialeSerializer(prestation_sociale).data}")
        

#class PrestationSocialeListCreateView(generics.ListCreateAPIView):
#    permission_classes = [permissions.IsAuthenticated]
#    queryset = PrestationSociale.objects.all().order_by('-date_soumission')
#    serializer_class = PrestationSocialeSerializer

#    def perform_create(self, serializer):
#        mutualiste = self.request.user.mutualiste
#        prestation_sociale = serializer.save(mutualiste=mutualiste)
#        print(PrestationSocialeSerializer(prestation_sociale).data)  # Debugging


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def liste_natures_prestations_sociales(request):
    """
    Récupère la liste des prestations sociales disponibles.
    """
    prestations = NaturePrestationSociale.objects.all()
    serializer = NaturePrestationSocialeSerializer(prestations, many=True)
    return Response(serializer.data)
