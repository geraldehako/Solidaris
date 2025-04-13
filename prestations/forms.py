from django import forms

from centres.models import CentreSantePrestation
from .models import ExamenMedical, Hospitalisation, ListeDesPrestations, Medicament, MedicamentPrescris, Prescription,Prestation, PrestationLunetterie, PriseEnCharge
from django.forms import inlineformset_factory, modelformset_factory

#================================================================================
class ListeDesPrestationsForm(forms.ModelForm):
    class Meta:
        model = ListeDesPrestations
        fields = ['nom', 'description', 'categorie', 'tarif_standard', 'actif', 'soumis_a_validation']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control','placeholder': 'Entrez le nom'}),
            'description': forms.Textarea(attrs={'class': 'form-control','placeholder': 'Entrez le descriptif'}),
            'categorie': forms.Select(attrs={'class': 'form-control'}),
            'tarif_standard': forms.NumberInput(attrs={'class': 'form-control','placeholder': 'Entrez le tarif'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'soumis_a_validation': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
 

#========================================================== ======================
# ✅ Formulaire pour un examen médical
class ExamenMedicalForm(forms.ModelForm):
    type_examen = forms.ModelChoiceField(
        queryset=ListeDesPrestations.objects.filter(categorie="analyse"),
        label="Type d'examen",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = ExamenMedical
        fields = ['type_examen', 'resultat_texte', 'fichier_resultat']
        widgets = {
            'resultat_texte': forms.Textarea(attrs={'class': 'form-control'}),
            'fichier_resultat': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['type_examen'].widget.attrs.update({
            'class': 'form-control select2'
        })


# ✅ Création du formset pour lier plusieurs examens à une prise en charge
ExamenMedicalFormSet = inlineformset_factory(
    PriseEnCharge, ExamenMedical,
    form=ExamenMedicalForm,
    extra=1,  # Nombre de formulaires supplémentaires à afficher
    can_delete=True
)

#✅ Formulaire pour un examen médical
class ExamenMedicalFormbon(forms.ModelForm):
    type_examen = forms.ModelChoiceField(
        queryset=ListeDesPrestations.objects.filter(categorie="analyse"),
        label="Type d'examen",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = ExamenMedical
        fields = ['type_examen', 'resultat_texte', 'fichier_resultat']
        widgets = {
            'resultat_texte': forms.Textarea(attrs={'class': 'form-control'}),
            'fichier_resultat': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


# ✅ Création du formset pour lier plusieurs examens à une prise en charge
ExamenMedicalFormSet = inlineformset_factory(
    PriseEnCharge, ExamenMedical,
    form=ExamenMedicalForm,
    extra=1,  # Nombre de formulaires supplémentaires à afficher
    can_delete=True
)

#================================================================================
# ✅ Formulaire pour Prestation
class PrestationForm(forms.ModelForm):
    prestation = forms.ModelChoiceField(
        queryset=CentreSantePrestation.objects.none(),
        label="Sélectionnez une prestation",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Prestation
        fields = ['prestation', 'description']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and hasattr(user, 'centre_sante') and user.centre_sante:
            self.fields['prestation'].queryset = CentreSantePrestation.objects.filter(
                centre_sante=user.centre_sante,
                prestation__categorie="analyse"
            )
        else:
            self.fields['prestation'].queryset = CentreSantePrestation.objects.none()

    def clean_prestation(self):
        prestation = self.cleaned_data.get('prestation')
        if not prestation:
            raise forms.ValidationError("Une prestation doit être sélectionnée.")
        return prestation


#================================================================================
class HospitalisationForm(forms.ModelForm):
    class Meta:
        model = Hospitalisation
        fields = [
            'prise_en_charge', 'mutualiste', 'centre_sante',
            'date_sortie', 'motif_hospitalisation', 'fichier_hospitalisation',
            'statut_prise_en_charge', 'montant_prise_en_charge', 'duree_validite'
        ]
        widgets = {
            'date_sortie': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'motif_hospitalisation': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'montant_prise_en_charge': forms.NumberInput(attrs={'class': 'form-control'}),
            'duree_validite': forms.NumberInput(attrs={'class': 'form-control'}),
            'statut_prise_en_charge': forms.Select(attrs={'class': 'form-control'}),
            'prise_en_charge': forms.Select(attrs={'class': 'form-control'}),
            'mutualiste': forms.Select(attrs={'class': 'form-control'}),
            'centre_sante': forms.Select(attrs={'class': 'form-control'}),
            'fichier_hospitalisation': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

#================================================================================
class MedicamentForm(forms.ModelForm):
    class Meta:
        model = Medicament
        fields = '__all__'
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Code du médicament'}),
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du médicament'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Description', 'rows': 2}),
            'dci': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'DCI'}),
            'molecule': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Molécule'}),
            'typem': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Type de médicament'}),
            'regime': forms.Select(attrs={'class': 'form-control'}),
            'disponible_en_pharmacie': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'cout_unitaire': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Coût unitaire'}),
        }

#================================================================================
class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['prise_en_charge', 'date_prescription']

class MedicamentPrescrisForm(forms.ModelForm):
    class Meta:
        model = MedicamentPrescris
        fields = ['medicament', 'quantite_prescrite', 'posologie', 'substitution_possible']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['medicament'].widget.attrs.update({
            'class': 'form-control select2'
        })

# Création du Formset pour MedicamentPrescris
MedicamentPrescrisFormSet = inlineformset_factory(
    Prescription, MedicamentPrescris,
    form=MedicamentPrescrisForm,
    extra=5,  # Nombre de formulaires vides affichés par défaut
    can_delete=True
)


#======================  FORMULAIRE DE VALIDATION ==========================================================
class HospitalisationValidationForm(forms.ModelForm):
    class Meta:
        model = Hospitalisation
        fields = ['statut_prise_en_charge','motif_refus']
        widgets = {
            'statut_prise_en_charge': forms.Select(choices=Hospitalisation.StatutPriseEnCharge.choices, attrs={'class': 'form-control'}),
            'motif_refus': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'motif du refus', 'rows': 3})
        }

class ExamenValidationForm(forms.ModelForm):
    class Meta:
        model = ExamenMedical
        fields = ['statut','motif_refus']
        widgets = {
            'statut': forms.Select(choices=ExamenMedical.StatutExamen.choices, attrs={'class': 'form-control'}),
            'motif_refus': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'motif du refus', 'rows': 3}),
        }

class OptiqueValidationForm(forms.ModelForm):
    class Meta:
        model = PrestationLunetterie
        fields = ['statut','motif_refus']
        widgets = {
            'statut': forms.Select(choices=PrestationLunetterie.StatutOptique.choices, attrs={'class': 'form-control'}),
            'motif_refus': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'motif du refus', 'rows': 3}),
        }