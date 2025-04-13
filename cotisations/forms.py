from django import forms
from .models import MouvementPaiement

class MouvementPaiementForm(forms.ModelForm):
    class Meta:
        model = MouvementPaiement 
        fields = ['montant', 'mode_paiement', 'reference','fichier_virement']
        widgets = {
            'montant': forms.NumberInput(attrs={'class': 'form-control','placeholder': 'Entrez le montant'}),
            'mode_paiement': forms.Select(attrs={'class': 'form-control'}),
            'reference': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'reference'}),
            'fichier_virement': forms.FileInput(attrs={'class': 'form-control'}),
        }
