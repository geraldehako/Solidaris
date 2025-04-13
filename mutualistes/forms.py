from django import forms
from django.forms import inlineformset_factory, TextInput, DateInput, Select, FileInput
from .models import Mutualiste, Beneficiaire,NaturePrestationSociale, PrestationSociale
from django.contrib import admin

class MutualisteForm(forms.ModelForm):
    class Meta:
        model = Mutualiste
        fields = [
            'photo', 'nom', 'prenom', 'date_naissance', 
            'sexe', 'regime', 'statut','groupe','telephone'
        ]
        widgets = {
            'photo': FileInput(attrs={'class': 'form-control'}),
            'nom': TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Entrez le nom'
            }),
            'prenom': TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Entrez le prénom'
            }),
            'telephone': TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Entrez le cellulaire'
            }),
            'date_naissance': DateInput(attrs={
                'class': 'form-control', 
                'type': 'date'
            }),
            'sexe': forms.Select(attrs={
                'class': 'form-select',
                'aria-label': 'Sélectionner le sexe',
            }),
            
            'regime': Select(attrs={
                'class': 'form-select'
            }),
            'groupe': Select(attrs={
                'class': 'form-select'
            }),
            'statut': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

class BeneficiaireForm(forms.ModelForm):
    class Meta:
        model = Beneficiaire
        fields = [
            'photo','nom', 'prenom', 'type_filiation', 
            'date_naissance', 'sexe'
        ]
        widgets = {
            'photo': FileInput(attrs={'class': 'form-control'}),
            'nom': TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Entrez le nom'
            }),
            'prenom': TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Entrez le prénom'
            }),
            'type_filiation': Select(attrs={
                'class': 'form-select'
            }),
            'date_naissance': DateInput(attrs={
                'class': 'form-control', 
                'type': 'date'
            }),
            'sexe': Select(attrs={
                'class': 'form-select'
            }),
        }

# Formset pour gérer plusieurs bénéficiaires
BeneficiaireFormSet = inlineformset_factory(
    Mutualiste, Beneficiaire, 
    form=BeneficiaireForm,
    extra=1,  # Nombre de bénéficiaires par défaut
    can_delete=True  # Possibilité de supprimer des bénéficiaires
)

# ============================= PRESTATIONS SOCIALES =========================================================================================================
from django import forms
from .models import NaturePrestationSociale, PrestationSociale

class NaturePrestationSocialeForm(forms.ModelForm):
    class Meta:
        model = NaturePrestationSociale
        fields = ['nature', 'montant']
        widgets = {
            'nature': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Entrez la nature de la prestation'
            }),
            'montant': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Entrez le montant'
            }),
        }

class PrestationSocialeForm(forms.ModelForm):
    class Meta:
        model = PrestationSociale
        fields = [
            'mutualiste', 'prestation_sociale', 'etat', 
            'date_soumission', 'date_validation', 
            'date_paiement', 'justification', 'preuve_paiement'
        ]
        widgets = {
            'mutualiste': forms.Select(attrs={'class': 'form-control'}),
            'prestation_sociale': forms.Select(attrs={'class': 'form-control'}),
            'etat': forms.Select(attrs={'class': 'form-control'}),
            'date_soumission': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'date_validation': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'date_paiement': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'justification': forms.FileInput(attrs={'class': 'form-control'}),
            'preuve_paiement': forms.FileInput(attrs={'class': 'form-control'}),
        }
        
class PrestationSociale_tts_Form(forms.ModelForm):
    class Meta:
        model = PrestationSociale
        fields = ['etat', 'date_validation']
        widgets = {
            'etat': forms.Select(attrs={'class': 'form-control'}),
            'date_validation': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date', 'placeholder': 'Date de validation'
            }),
        }

