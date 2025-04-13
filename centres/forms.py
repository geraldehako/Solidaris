from django import forms
from .models import CentreSante, CentreSantePrestation, Groupe, MedecinTraitant
from prestations.models import ListeDesPrestations

# ========================================== GROUPES =================================================================================================================
class GroupeForm(forms.ModelForm):
    class Meta:
        model = Groupe
        fields = ['nom', 'description']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom un(e) ville/localité/groupe'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Description', 'rows': 3})
        }

# ==============================================  CENTRE SANTE  ======================================================================================================= 
class CentreSanteForm(forms.ModelForm):
    prestations = forms.ModelMultipleChoiceField(
        queryset=ListeDesPrestations.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Prestations disponibles",
    ) 

    class Meta: 
        model = CentreSante
        fields = ['nom', 'type', 'adresse', 'telephone', 'email', 'groupe']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du prestataire'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Adresse'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'telephone'}),
            'email': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'email'}),
            'groupe': forms.Select(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),

        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Vous pouvez ajouter des fonctionnalités dynamiques ici, comme filtrer les prestations
        self.fields['prestations'].queryset = ListeDesPrestations.objects.filter(categorie="consultation")

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        # Traitez les prestations associées
        prestations = self.cleaned_data.get('prestations', [])
        for prestation in prestations:
            CentreSantePrestation.objects.get_or_create(
                centre_sante=instance,
                prestation=prestation,
                defaults={'tarif_personnalise': None, 'disponible': True}
            )
        return instance
    
    
# =====================================================  MEDECIN TRAITANT ======================================================================================

class MedecinTraitantForm(forms.ModelForm):
    class Meta:
        model = MedecinTraitant
        fields = ["nom", "prenom", "specialite", "email", "telephone", "centre_sante"]


#  ==================================================  


class CentreSanteFormplus(forms.ModelForm):
    prestations = forms.ModelMultipleChoiceField(
        queryset=ListeDesPrestations.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Prestations disponibles",
    )
    tarifs_personnalises = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
        label="Tarifs personnalisés (JSON)"
    )

    class Meta:
        model = CentreSante
        fields = ['nom', 'type', 'adresse', 'telephone', 'email', 'groupe']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['prestations'].queryset = ListeDesPrestations.objects.all()

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()

        prestations = self.cleaned_data.get('prestations', [])
        tarifs_personnalises = self.cleaned_data.get('tarifs_personnalises', '{}')
        
        import json
        tarifs = json.loads(tarifs_personnalises)

        # Associez les prestations avec leurs tarifs personnalisés
        for prestation in prestations:
            tarif_personnalise = tarifs.get(str(prestation.id), None)
            CentreSantePrestation.objects.update_or_create(
                centre_sante=instance,
                prestation=prestation,
                defaults={
                    'tarif_personnalise': tarif_personnalise,
                    'disponible': True
                }
            )

        return instance
