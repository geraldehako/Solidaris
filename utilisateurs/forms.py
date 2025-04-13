from django import forms
from .models import Utilisateur

class UtilisateurForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False)

    class Meta:
        model = Utilisateur
        fields = ['username', 'password']
    widgets = {
        'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Nom d'utilisateur"}),
    }
 

from django import forms
from .models import Utilisateur

class UtilisateuraddForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mot de passe'}),
        required=True
    )
    # Restriction des choix de rôle
    role = forms.ChoiceField(
        choices=[  
            ('gestionnaire', 'Gestionnaire'),
            ('point_focal', 'Point Focal'),
            ('medecin_conseil', 'Médecin Conseil')
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True  # Rend ce champ obligatoire
    )

    class Meta:
        model = Utilisateur
        fields = ['username', 'password', 'role', 'telephone', 'photo', 'groupe', 'last_name', 'first_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Nom d'utilisateur"}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numéro de téléphone'}),
            'groupe': forms.Select(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de famille'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

