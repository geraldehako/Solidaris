from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from .models import CentreSante, CentreSantePrestation
from .forms import CentreSanteForm
from prestations.models import ListeDesPrestations
from django.template.loader import render_to_string

def ajouter_centre_sante1(request, pk=None):
    instance = get_object_or_404(CentreSante, pk=pk) if pk else None
    form = CentreSanteForm(request.POST or None, instance=instance)
    prestations = ListeDesPrestations.objects.all()

    # Recherche et filtrage
    categorie = request.GET.get('categorie')
    recherche = request.GET.get('recherche')

    if categorie:
        prestations = prestations.filter(categorie=categorie)

    if recherche:
        prestations = prestations.filter(description__icontains=recherche)

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('liste_centre_sante')  # Redirection après enregistrement

    context = {
        'form': form,
        'prestations': prestations,
        'instance': instance,
    }
    return render(request, 'backoffice/centresantes/ajouter_centre_sante.html', context)

def ajouter_centre_santeokun(request):
    if request.method == 'POST':
        form = CentreSanteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('liste_centre_sante')  # Remplacez par la vue de redirection
    else:
        form = CentreSanteForm()

    # Récupérer les catégories des prestations
    categories_prestation = ListeDesPrestations.CATEGORIES_PRESTATION

    return render(request, 'backoffice/centresantes/ajouter_centre_sante.html', {
        'form': form,
        'categories_prestation': categories_prestation
    })

from django.shortcuts import render, redirect
from .forms import CentreSanteForm
from prestations.models import ListeDesPrestations

def ajouter_centre_sante(request):
    if request.method == 'POST':
        form = CentreSanteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('nom_de_votre_vue_de_redirection')
        else:
            # Ajoutez ceci pour déboguer en cas d'erreur dans le formulaire
            print(form.errors)
    else:
        form = CentreSanteForm()

    prestations = ListeDesPrestations.CATEGORIES_PRESTATION

    return render(request, 'backoffice/centresantes/ajouter_centre_sante.html', {
        'form': form,
        'prestations': prestations,
    })

def save(self, commit=True):
    instance = super().save(commit=False)
    if commit:
        instance.save()

    prestations = self.cleaned_data.get('prestations', [])  # Prestations sélectionnées

    for prestation in prestations:
        # Récupération des tarifs personnalisés directement dans les données POST
        tarif_personnalise = self.data.get(f'tarifs_personnalises_{prestation.id}', None)
        
        # Mise à jour ou création de la relation CentreSantePrestation
        CentreSantePrestation.objects.update_or_create(
            centre_sante=instance,
            prestation=prestation,
            defaults={
                'tarif_personnalise': tarif_personnalise,
                'disponible': True
            }
        )

    return instance


from django.http import JsonResponse
from django.template.loader import render_to_string

def filtrer_prestations(request):
    categorie = request.GET.get('categorie', '')
    recherche = request.GET.get('recherche', '')

    # Filtrer les prestations
    prestations = ListeDesPrestations.objects.all()
    if categorie:
        prestations = prestations.filter(categorie=categorie)
    if recherche:
        prestations = prestations.filter(nom__icontains=recherche)

    # Rendu partiel pour les lignes du tableau
    html = render_to_string('backoffice/centresantes/prestations_partials.html', {'prestations': prestations})
    return JsonResponse({'html': html})


def filtrer_prestationsokun(request):
    # Récupérer les paramètres de filtrage
    categorie = request.GET.get('categorie')
    recherche = request.GET.get('recherche')

    # Appliquer les filtres
    prestations = ListeDesPrestations.objects.all()
    if categorie:
        prestations = prestations.filter(categorie=categorie)
    if recherche:
        prestations = prestations.filter(description__icontains=recherche)

    # Générer le HTML partiel pour les prestations
    html = render_to_string('backoffice/centresantes/prestations_partials.html', {'prestations': prestations})
    return JsonResponse({'html': html})