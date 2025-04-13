from datetime import date
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required

from prestations.models import Prestation, PrestationPharmacie
from .models import Facture

@login_required
def liste_factures(request):
    """
    Affiche la liste des factures du centre connecté.
    """
    centre_sante = request.user.centre_sante
    factures = Facture.objects.filter(centre=centre_sante).order_by('-date_emission')
    
    return render(request, "frontoffice/factures/liste_factures.html", {"factures": factures})

@login_required
def factures_impayees_anterieures(request):
    # Obtenir le premier jour du mois en cours
    premier_jour_mois = date.today().replace(day=1)

    # Filtrer les factures impayées et antérieures au mois en cours
    factures = Facture.objects.filter(
        statut='impayee',
        date_debut__lt=premier_jour_mois
    )

    return render(request, "backoffice/factures/facture_list.html", {"factures": factures})

@login_required
def factures_payees_anterieures(request):
    # Obtenir le premier jour du mois en cours
    premier_jour_mois = date.today().replace(day=1)

    # Filtrer les factures payées et antérieures au mois en cours
    factures = Facture.objects.filter(
        statut='payee',
        date_debut__lt=premier_jour_mois
    )

    return render(request, "backoffice/factures/facture_list.html", {"factures": factures})

from datetime import date

@login_required
def factures_impayees_encours(request):
    # Obtenir le premier jour du mois en cours
    premier_jour_mois = date.today().replace(day=1)

    # Filtrer les factures impayées et du mois en cours
    factures = Facture.objects.filter(
        statut='impayee',  # Si tu veux les impayées et non 'payee'
        date_debut__gte=premier_jour_mois  # Filtrer uniquement le mois en cours
    )

    return render(request, "backoffice/factures/facture_list.html", {"factures": factures})


@login_required
def toggle_factures_status(request, facture_id):
    facture = get_object_or_404(Facture, id=facture_id)

    # Vérifie si `statut` est un champ texte
    if facture.statut == "payée":
        facture.statut = "impayée"
    else:
        facture.statut = "payée"
    
    facture.save()
    
    messages.success(request, f"Le statut de la facture {facture.numero_facture} a été mis à jour.")
    return redirect('factures_impayees')  # Vérifie si cette URL est correcte


@login_required
def liste_facturespharmacie(request):
    """
    Affiche la liste des factures du centre connecté.
    """
    centre_sante = request.user.centre_sante
    factures = Facture.objects.filter(centre=centre_sante).order_by('-date_emission')
    
    return render(request, "frontoffice/factures/liste_facturespharmacie.html", {"factures": factures})


@login_required
def detail_facture(request, facture_id):
    """
    Affiche les détails d'une facture avec les prestations rattachées au centre et filtrées par la période de la facture.
    """
    facture = get_object_or_404(Facture, id=facture_id, centre=request.user.centre_sante)

    # Filtrer les prestations appartenant au centre et dont la date correspond à la facture
    prestations = Prestation.objects.filter(
        centre_sante=facture.centre,
        date_prestation__range=[facture.date_debut, facture.date_fin]
    ).order_by('-date_prestation')

    return render(request, "frontoffice/factures/detail_facture.html", {
        "facture": facture,
        "prestations": prestations
    })

@login_required
def detail_facturepharmacie(request, facture_id):
    """
    Affiche les détails d'une facture avec les prestations rattachées au centre et filtrées par la période de la facture.
    """
    facture = get_object_or_404(Facture, id=facture_id, centre=request.user.centre_sante)

    # Filtrer les prestations appartenant au centre et dont la date correspond à la facture
    prestations = PrestationPharmacie.objects.filter(
        centre_sante=facture.centre,
        date_prestation__range=[facture.date_debut, facture.date_fin]
    ).order_by('-date_prestation')

    return render(request, "frontoffice/factures/detail_facturepharmacie.html", {
        "facture": facture,
        "prestations": prestations
    })