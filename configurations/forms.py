from django import forms
from .models import CategorieAffection

class CategorieAffectionForm(forms.ModelForm):
    class Meta:
        model = CategorieAffection
        fields = ['nom', 'description']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de la catégorie'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description'}),
        }

from .models import CodeAffection, Ordonnance

class CodeAffectionForm(forms.ModelForm):
    class Meta:
        model = CodeAffection
        fields = ['code', 'nom', 'description', 'categorie']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'categorie': forms.Select(attrs={'class': 'form-control'}),
        }

class OrdonnanceForm(forms.ModelForm):
    class Meta:
        model = Ordonnance
        fields = ['mutualiste', 'renouvelable', 'periodicite', 'valide_jusquau']
        widgets = {
            'mutualiste': forms.Select(attrs={'class': 'form-control'}),
            'renouvelable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'periodicite': forms.NumberInput(attrs={'class': 'form-control'}),
            'valide_jusquau': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
