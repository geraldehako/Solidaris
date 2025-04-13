from django.shortcuts import redirect, render
from .models import Cotisation, MouvementPaiement
from django.shortcuts import get_object_or_404
from .forms import MouvementPaiementForm

def liste_cotisations(request):
    cotisations = Cotisation.objects.all()
    return render(request, 'backoffice/cotisations/liste_cotisations.html', {'cotisations': cotisations})

def liste_paiements(request, cotisation_id):
    paiements = MouvementPaiement.objects.filter(cotisation=cotisation_id)
    return render(request, 'backoffice/paiements/liste_paiements.html', {'paiements': paiements})

def ajouter_paiement(request, cotisation_id):
    cotisation = get_object_or_404(Cotisation, id=cotisation_id)

    if request.method == 'POST':
        form = MouvementPaiementForm(request.POST)
        if form.is_valid():
            paiement = form.save(commit=False)
            paiement.cotisation = cotisation
            paiement.created_by = request.user
            paiement.save()

            # Mettre à jour les totaux après l'ajout d'un paiement
            cotisation.total_payer += paiement.montant
            cotisation.calculer_totaux()

            return redirect('liste_cotisations')

    else:
        form = MouvementPaiementForm()

    return render(request, 'backoffice/paiements/ajouter_paiement.html', {'form': form, 'cotisation': cotisation})


def modifier_paiement(request, paiement_id):
    paiement = get_object_or_404(MouvementPaiement, id=paiement_id)
    cotisation = paiement.cotisation
    ancien_montant = paiement.montant  # Sauvegarde de l'ancien montant

    if request.method == 'POST':
        form = MouvementPaiementForm(request.POST, instance=paiement)
        if form.is_valid():
            paiement = form.save()

            # Ajuster total_payer en fonction de la différence de montant
            difference = paiement.montant - ancien_montant
            cotisation.total_payer += difference
            cotisation.calculer_totaux()

            return redirect('liste_paiements')

    else:
        form = MouvementPaiementForm(instance=paiement)

    return render(request, 'backoffice/paiements/modifier_paiement.html', {'form': form})


def supprimer_paiement(request, paiement_id):
    paiement = get_object_or_404(MouvementPaiement, id=paiement_id)
    cotisation = paiement.cotisation

    if request.method == 'POST':
        montant_supprime = paiement.montant
        paiement.delete()

        # Mettre à jour les totaux après la suppression
        cotisation.total_payer -= montant_supprime
        cotisation.calculer_totaux()

        return redirect('liste_paiements')

    return render(request, 'backoffice/paiements/supprimer_paiement.html', {'paiement': paiement})

