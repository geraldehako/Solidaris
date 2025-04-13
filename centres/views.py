from collections import defaultdict
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from .models import CentreSante, CentreSantePrestation, Groupe
from .forms import CentreSanteForm, GroupeForm
from prestations.models import ListeDesPrestations
from django.template.loader import render_to_string

from django.views.generic import ListView
from django.shortcuts import render
from .models import CentreSante
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError

from .models import CentreSantePrestation, CentreSante
from prestations.models import ListeDesPrestations

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import CentreSante  # Remplacez par le nom exact de votre modèle
from prestations.models import ListeDesPrestations
from django.template.loader import render_to_string
from django.http import JsonResponse
from prestations.models import ListeDesPrestations

# ===================================================   GROUPES   ==================================================================================================
def liste_groupes(request):
    groupes = Groupe.objects.all().order_by('nom')
    return render(request, 'backoffice/groupes/liste_groupes.html', {'groupes': groupes})

# Ajouter un groupe
def ajouter_groupe(request):
    if request.method == 'POST':
        form = GroupeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('liste_groupes')
    else:
        form = GroupeForm()
    return render(request, 'backoffice/groupes/ajouter_groupe.html', {'form': form})

# Modifier un groupe
def modifier_groupe(request, groupe_id):
    groupe = get_object_or_404(Groupe, id=groupe_id)
    if request.method == 'POST':
        form = GroupeForm(request.POST, instance=groupe)
        if form.is_valid():
            form.save()
            return redirect('liste_groupes')
    else:
        form = GroupeForm(instance=groupe)
    return render(request, 'backoffice/groupes/modifier_groupe.html', {'form': form, 'groupe': groupe})

# Supprimer un groupe
def supprimer_groupe(request, groupe_id):
    groupe = get_object_or_404(Groupe, id=groupe_id)
    if request.method == 'POST':
        groupe.delete()
        return redirect('liste_groupes')
    return render(request, 'backoffice/groupes/supprimer_groupe.html', {'groupe': groupe})

# ===================================================   CENTRES   ==================================================================================================
def liste_centres_actifs(request):
    centres_groupes = defaultdict(list)
    centres = CentreSante.objects.filter(statut=True).order_by('type')

    # for centre in centres_actifs:
    #     centres_groupes[centre.type].append(centre)

    return render(request, 'backoffice/centresantes/centres_actifs.html', {'centres': centres})

def liste_centres_nonactifs(request):
    centres_groupes = defaultdict(list)
    centres = CentreSante.objects.filter(statut=False).order_by('type')

    # for centre in centres_actifs:
    #     centres_groupes[centre.type].append(centre)

    return render(request, 'backoffice/centresantes/centres_actifs.html', {'centres': centres})

class ListeCentreSanteView(ListView):
    model = CentreSante
    template_name = 'backoffice/centresantes/liste_centre_sante.html'
    context_object_name = 'centres'
    paginate_by = 10  # Nombre de centres par page

    def get_queryset(self):
        queryset = CentreSante.objects.all().order_by('nom')  # Trier par nom
        recherche = self.request.GET.get('recherche', '')
        if recherche:
            queryset = queryset.filter(nom__icontains=recherche)  # Recherche par nom
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recherche'] = self.request.GET.get('recherche', '')  # Préserver le champ de recherche
        return context


from utilisateurs.models import Utilisateur
from django.contrib.auth import get_user_model
def ajouter_centre_sante(request):
    if request.method == 'POST':
        form = CentreSanteForm(request.POST)
        if form.is_valid():
            # Sauvegarde du centre de santé 
            centre_sante = form.save()

            # Création d'un utilisateur pour ce centre de santé
            groupe = form.cleaned_data['groupe']
            telephone = form.cleaned_data['telephone']
            utilisateur = get_user_model().objects.create_user(
                username=centre_sante.nom.lower(),  # Utiliser le nom du centre de santé pour le nom d'utilisateur
                password="P@ssword",  # Vous pouvez définir un mot de passe par défaut ou générer un mot de passe
                role='centre_sante',  # Le rôle de l'utilisateur est 'centre_sante'
                centre_sante=centre_sante,  # Associe l'utilisateur au centre de santé créé
                telephone=telephone,
                groupe=groupe,
                last_name=centre_sante.nom.lower(),
                first_name=centre_sante.nom.lower(),
            )

            # Message de succès
            messages.success(request, "Centre de santé ajouté avec succès et utilisateur créé.")
            return redirect('liste_centre_sante')  # Remplacez par la vue de redirection

    else:
        form = CentreSanteForm()

    # Récupérer les catégories des prestations
    categories_prestation = ListeDesPrestations.CATEGORIES_PRESTATION

    return render(request, 'backoffice/centresantes/ajouter_centre_sante.html', {
        'form': form,
        'categories_prestation': categories_prestation
    })


@require_POST
def centre_sante_delete(request, pk):
    """
    Supprime un centre de santé à partir de son identifiant (pk).
    """
    # Récupérer le centre de santé ou retourner une 404 s'il n'existe pas
    centre = get_object_or_404(CentreSante, pk=pk)
    
    # Suppression du centre
    centre.delete()
    
    # Ajout d'un message de succès
    messages.success(request, "Le centre de santé a été supprimé avec succès.")
    
    # Redirection vers la liste des centres
    return redirect(reverse('liste_centre_sante'))  # Remplacez 'liste_centres' par le nom de votre URL de liste


def toggle_centre_status(request, centre_id):
    centre = get_object_or_404(CentreSante, id=centre_id)
    centre.statut = not centre.statut  # Bascule entre actif et inactif
    centre.save()
    messages.success(request, f"Le statut de {centre.nom} a été mis à jour.")
    return redirect('liste_centre_sante')  # Redirige vers la liste des centres


def filtrer_prestations(request):
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



def importer_prestationscentre1(request):
    """
    Vue pour importer un fichier Excel contenant les associations entre centres de santé et prestations.
    """
    if request.method == "POST" and request.FILES.get("file"):
        fichier_excel = request.FILES["file"]

        try:
            # Lire le fichier Excel avec pandas
            df = pd.read_excel(fichier_excel)

            # Valider que les colonnes nécessaires existent
            colonnes_attendues = ["centre_sante", "prestation", "tarif_personnalise", "disponible"]
            if not all(colonne in df.columns for colonne in colonnes_attendues):
                messages.error(request, "Le fichier Excel doit contenir les colonnes : centre_sante, prestation, tarif_personnalise, disponible.")
                return redirect("importer_prestations")

            # Parcourir les lignes du fichier et créer les objets
            for _, row in df.iterrows():
                try:
                    centre_sante = CentreSante.objects.get(nom=row["centre_sante"])
                    prestation = ListeDesPrestations.objects.get(nom=row["prestation"])
                    tarif_personnalise = row["tarif_personnalise"]
                    disponible = row["disponible"]

                    # Créer ou mettre à jour l'association
                    obj, created = CentreSantePrestation.objects.update_or_create(
                        centre_sante=centre_sante,
                        prestation=prestation,
                        defaults={
                            "tarif_personnalise": tarif_personnalise,
                            "disponible": disponible,
                        },
                    )
                except CentreSante.DoesNotExist:
                    messages.warning(request, f"Centre de santé '{row['centre_sante']}' introuvable.")
                except ListeDesPrestations.DoesNotExist:
                    messages.warning(request, f"Prestation '{row['prestation']}' introuvable.")
                except ValidationError as e:
                    messages.error(request, f"Erreur de validation : {e}")

            messages.success(request, "Importation terminée avec succès.")
            return redirect("liste_centre_sante")

        except Exception as e:
            messages.error(request, f"Erreur lors de l'importation : {e}")
            return redirect("importer_prestations")

    return render(request, "backoffice/centresantes/importer_prestations.html")



def importer_prestationscentre2(request):
    """
    Vue pour importer un fichier Excel contenant les associations entre centres de santé et prestations.
    """
    if request.method == "POST" and request.FILES.get("file"):
        fichier_excel = request.FILES["file"]

        try:
            # Lire le fichier Excel avec pandas
            df = pd.read_excel(fichier_excel)

            # Valider que les colonnes nécessaires existent
            colonnes_attendues = ["centre_sante", "prestation", "tarif_personnalise", "disponible"]
            if not all(colonne in df.columns for colonne in colonnes_attendues):
                messages.error(request, "Le fichier Excel doit contenir les colonnes : centre_sante, prestation, tarif_personnalise, disponible.")
                return redirect("importer_prestations")

            # Parcourir les lignes du fichier et créer les objets
            for _, row in df.iterrows():
                try:
                    # Récupérer le centre de santé
                    centre_sante = CentreSante.objects.filter(nom=row["centre_sante"]).first()
                    if not centre_sante:
                        messages.warning(request, f"Centre de santé '{row['centre_sante']}' introuvable.")
                        continue  # Passer à la ligne suivante

                    # Récupérer la prestation
                    prestation = ListeDesPrestations.objects.filter(nom=row["prestation"]).first()
                    if not prestation:
                        messages.warning(request, f"Prestation '{row['prestation']}' introuvable.")
                        continue  # Passer à la ligne suivante

                    # Extraire les données
                    tarif_personnalise = row["tarif_personnalise"]
                    disponible = row["disponible"]

                    # Créer ou mettre à jour l'association
                    obj, created = CentreSantePrestation.objects.update_or_create(
                        centre_sante=centre_sante,
                        prestation=prestation,
                        defaults={
                            "tarif_personnalise": tarif_personnalise,
                            "disponible": disponible,
                        },
                    )

                except ValidationError as e:
                    messages.error(request, f"Erreur de validation sur la ligne {row.name + 1} : {e}")
                except Exception as e:
                    messages.error(request, f"Erreur lors du traitement de la ligne {row.name + 1}: {e}")

            messages.success(request, "Importation terminée avec succès.")
            return redirect("liste_centre_sante")

        except Exception as e:
            messages.error(request, f"Erreur lors de l'importation du fichier : {e}")
            return redirect("importer_prestations")

    return render(request, "backoffice/centresantes/importer_prestations.html")

def importer_prestationscentre(request):
    if request.method == 'POST':
        fichier_excel = request.FILES.get('fichier_excel')
        
        if not fichier_excel:
            messages.error(request, "Veuillez sélectionner un fichier Excel.")
            return redirect('importer_prestationscentre')
        
        try:
            # Lire le fichier Excel avec pandas
            df = pd.read_excel(fichier_excel)

            # Vérifier que le fichier contient les colonnes nécessaires
            colonnes_requises = ['centre_sante', 'prestation', 'tarif_personnalise', 'disponible']
            if not all(colonne in df.columns for colonne in colonnes_requises):
                messages.error(request, "Le fichier Excel doit contenir les colonnes suivantes : " + ", ".join(colonnes_requises))
                return redirect('importer_prestationscentre')

            # Parcourir les lignes et créer des objets `CentreSantePrestation`
            for _, row in df.iterrows():
                # Récupérer le CentreSante basé sur le nom
                try:
                    centre_sante = CentreSante.objects.get(id=row['centre_sante'])
                except CentreSante.DoesNotExist:
                    messages.warning(request, f"Le centre de santé '{row['centre_sante']}' n'existe pas.")
                    continue  # Passer à la ligne suivante

                # Récupérer la prestation basée sur le nom
                try:
                    prestation = ListeDesPrestations.objects.get(id=row['prestation'])
                except ListeDesPrestations.DoesNotExist:
                    messages.warning(request, f"La prestation '{row['prestation']}' n'existe pas.")
                    continue  # Passer à la ligne suivante

                # Créer l'objet CentreSantePrestation
                CentreSantePrestation.objects.create(
                    centre_sante=centre_sante,
                    prestation=prestation,
                    tarif_personnalise=row['tarif_personnalise'],
                    disponible=row['disponible']
                )
            
            messages.success(request, "Les prestations ont été importées avec succès !")
            return redirect('liste_centre_sante')

        except Exception as e:
            messages.error(request, f"Erreur lors de l'importation du fichier : {e}")
            return redirect('importer_prestationscentre')

    return render(request, 'backoffice/centresantes/importer_prestations.html')



import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.contrib.auth import get_user_model
from .models import CentreSante, Groupe

def importer_centres_sante(request):
    if request.method == 'POST' and request.FILES.get('fichier'):
        fichier_excel = request.FILES['fichier']
        fs = FileSystemStorage()
        nom_fichier = fs.save(fichier_excel.name, fichier_excel)
        chemin_fichier = fs.path(nom_fichier)

        try:
            df = pd.read_excel(chemin_fichier)
            print("📄 Colonnes Excel :", list(df.columns))
            print("🔍 Premières lignes :", df.head())

            for index, row in df.iterrows():
                try:
                    print(f"\n📥 Traitement ligne {index + 2} : {row.to_dict()}")

                    # Vérification du type
                    type_centre = row['type'].strip().lower()
                    if type_centre not in dict(CentreSante.TYPES_CENTRE).keys():
                        messages.warning(request, f"Ligne {index + 2} : type de centre invalide : {type_centre}")
                        continue

                    # Récupération du groupe
                    try:
                        groupe = Groupe.objects.get(id=row['groupe'])
                    except Groupe.DoesNotExist:
                        messages.warning(request, f"Ligne {index + 2} : groupe ID={row['groupe']} introuvable.")
                        continue

                    # Création du centre
                    centre, created = CentreSante.objects.get_or_create(
                        nom=row['nom'],
                        defaults={
                            'type': type_centre,
                            'adresse': row['adresse'],
                            'telephone': str(row['telephone']),
                            'email': row.get('email', ''),
                            'groupe': groupe,
                            'statut': True,
                            'observations': row.get('observations', 'R.A.S')
                        }
                    )

                    if created:
                        # Création d'un utilisateur pour ce centre
                        get_user_model().objects.create_user(
                            username=centre.nom.lower().replace(' ', '_'),
                            password='P@ssword',
                            role='centre_sante',
                            centre_sante=centre,
                            telephone=centre.telephone,
                            groupe=groupe,
                            first_name=centre.nom,
                            last_name=centre.nom
                        )
                        messages.success(request, f"✅ {centre.nom} importé avec succès et utilisateur créé.")
                    else:
                        messages.info(request, f"ℹ️ {centre.nom} existe déjà, non recréé.")

                except Exception as e:
                    print(f"❌ Erreur ligne {index + 2} : {e}")
                    messages.error(request, f"❌ Erreur ligne {index + 2} : {str(e)}")

            return redirect('liste_centre_sante')

        except Exception as e:
            messages.error(request, f"❌ Erreur de traitement du fichier : {str(e)}")

    return render(request, 'backoffice/centresantes/importer_centres_sante.html')





from django.shortcuts import render, redirect
from .models import MedecinTraitant
from .forms import MedecinTraitantForm

def ajouter_medecin(request):
    if request.method == "POST":
        form = MedecinTraitantForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("liste_medecins")  # Rediriger vers la liste des médecins
    else:
        form = MedecinTraitantForm()

    return render(request, "frontoffice/medecins/ajouter_medecin.html", {"form": form})
