from centres.models import CentreSante
from facturations.models import Remboursement
from mutualistes.models import Beneficiaire, Mutualiste, NaturePrestationSociale, PrestationSociale
from prestations.models import Prestation, PrestationPharmacie
from rest_framework import serializers # type: ignore

class CentreSanteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CentreSante
        fields = '__all__'



class BeneficiaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Beneficiaire
        fields = ['code_matricule', 'nom', 'prenom', 'type_filiation']

class MutualisteSerializer(serializers.ModelSerializer):
    beneficiaires = BeneficiaireSerializer(many=True, read_only=True)

    class Meta:
        model = Mutualiste
        fields = ['code_matricule', 'nom', 'prenom', 'beneficiaires']


# Exemple de sérialiseur pour la Prestation
class PrestationSerializer(serializers.ModelSerializer):
    prestation_nom = serializers.CharField(source='prestation.nom', read_only=True)  # Ajout du nom de la prestation

    class Meta:
        model = Prestation
        #fields = ['id', 'prestation_nom', 'date_prestation', 'montant_total', 'montant_pris_en_charge', 'montant_moderateur', 'status', 'prestation']
        fields = ['id', 'prestation_nom','date_prestation', 'montant_total', 'montant_pris_en_charge', 'montant_moderateur', 
                  'tiers_payant', 'description', 'statut_validation', 'date_validation', 'prise_en_charge', 
                  'centre_sante', 'prestation', 'medecin_traitant']



class PrestationSocialeSerializer(serializers.ModelSerializer):
    # Ajoute des informations supplémentaires si nécessaire
    mutualiste = serializers.StringRelatedField(read_only=True)  # Affiche le nom du mutualiste
    prestation_sociale = serializers.StringRelatedField(read_only=True)  # Affiche la prestation sociale liée
    justification = serializers.FileField(required=False)  # Gère le fichier de justification, non obligatoire
    preuve_paiement = serializers.FileField(required=False)  # Gère le fichier de preuve de paiement, non obligatoire

    class Meta:
        model = PrestationSociale
        fields = ['id', 'mutualiste', 'prestation_sociale', 'etat', 'date_soumission', 'date_validation', 
                  'date_paiement', 'justification', 'preuve_paiement']
        read_only_fields = ['id', 'mutualiste']  # Les champs qui ne doivent pas être modifiés par l'utilisateur

    def validate_etat(self, value):
        """Validation personnalisée pour le champ 'etat'"""
        if value not in dict(PrestationSociale.ETATS_PRESTATION).keys():
            raise serializers.ValidationError("L'état de la prestation sociale n'est pas valide.")
        return value

    def create(self, validated_data):
        """Personnalisation de la création pour lier l'utilisateur connecté"""
        # Lier la prestation sociale au mutualiste connecté (utilisateur actuel)
        validated_data['mutualiste'] = self.context['request'].user.mutualiste
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Personnalisation de la mise à jour de la prestation sociale"""
        # Si nécessaire, mettre à jour d'autres champs ici
        instance = super().update(instance, validated_data)
        return instance


class PrestationPharmacieSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrestationPharmacie
        fields = '__all__'



class RemboursementSerializer(serializers.ModelSerializer):
    mutualiste_nom = serializers.CharField(source="mutualiste.utilisateur.username", read_only=True)

    class Meta:
        model = Remboursement
        fields = ['id', 'mutualiste_nom', 'montant', 'date_remboursement', 'statut', 'justif']


class NaturePrestationSocialeSerializer(serializers.ModelSerializer):
    class Meta:
        model = NaturePrestationSociale
        fields = ['id', 'nature']