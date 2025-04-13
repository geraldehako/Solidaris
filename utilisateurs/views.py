from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from .models import Utilisateur
from .forms import UtilisateurForm, UtilisateuraddForm  # À créer (voir section 5)

@login_required
def liste_utilisateurs(request):
    utilisateurs = Utilisateur.objects.all()
    return render(request, 'backoffice/utilisateurs/liste_utilisateurs.html', {'utilisateurs': utilisateurs}) 

@login_required
def ajouter_utilisateur(request):
    if request.method == 'POST':
        form = UtilisateuraddForm(request.POST, request.FILES)
        if form.is_valid():
            utilisateur = form.save(commit=False)
            utilisateur.password = make_password(form.cleaned_data['password'])  # Hachage du mot de passe
            utilisateur.save()
            messages.success(request, "Utilisateur ajouté avec succès.")
            return redirect('liste_utilisateurs')
    else:
        form = UtilisateuraddForm()

    return render(request, 'backoffice/utilisateurs/ajouter_utilisateur.html', {'form': form})

@login_required
def modifier_utilisateur(request, user_id):
    utilisateur = get_object_or_404(Utilisateur, id=user_id)

    if request.method == 'POST':
        form = UtilisateurForm(request.POST, instance=utilisateur)
        if form.is_valid():
            user = form.save(commit=False)
            
            # Hachage du mot de passe s'il est modifié
            if form.cleaned_data['password']:
                user.password = make_password(form.cleaned_data['password'])

            user.save()
            messages.success(request, "Utilisateur mis à jour avec succès.")
            return redirect('liste_utilisateurs')
    else:
        form = UtilisateurForm(instance=utilisateur)

    return render(request, 'backoffice/utilisateurs/modifier_utilisateur.html', {'form': form})

@login_required
def supprimer_utilisateur(request, user_id):
    utilisateur = get_object_or_404(Utilisateur, id=user_id)

    if request.method == 'POST':
        utilisateur.delete()
        messages.success(request, "Utilisateur supprimé avec succès.")
        return redirect('liste_utilisateurs')

    return render(request, 'backoffice/utilisateurs/confirm_suppression.html', {'utilisateur': utilisateur})

def reinitialiser_mot_de_passe(request, user_id):
    utilisateur = get_object_or_404(Utilisateur, id=user_id)
    if request.method == "POST":
        nouveau_mot_de_passe = request.POST.get("nouveau_mot_de_passe")
        utilisateur.password = make_password(nouveau_mot_de_passe)  # Hachage sécurisé
        utilisateur.save()
        return redirect('liste_utilisateurs')  # Redirection après mise à jour
    return render(request, "backoffice/utilisateurs/reinitialiser_mot_de_passe.html", {"utilisateur": utilisateur})
