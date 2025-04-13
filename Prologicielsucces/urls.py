"""Prologicielsucces URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls.static import static
from Prologicielsucces import settings
from configurations.views import (
    LoginView, PrestationSocialeListCreateView, RegisterView, ajouter_categorie, centre_sante_dashboard_view, code_affection_create, code_affection_delete, code_affection_list, code_affection_update, dashboard_medecin, dashboard_point_focal, get_prise_en_charge_events, liste_categories, liste_natures_prestations_sociales, login_view, logout_view, modifier_categorie, optique_dashboard_view, ordonnance_create, ordonnance_delete, ordonnance_list, ordonnance_update, point_focal, point_focal_cotisations, point_focal_dispensations, point_focal_mutualiste, point_focal_paiements, point_focal_prestataire, point_focal_prestations, supprimer_categorie, tableau_de_bord, tableau_de_bord_pharmacie
)
from cotisations.views import ajouter_paiement, liste_cotisations, liste_paiements, modifier_paiement, supprimer_paiement
from facturations.views import detail_facture, detail_facturepharmacie, factures_impayees_anterieures, factures_impayees_encours, factures_payees_anterieures, liste_factures, liste_facturespharmacie, toggle_factures_status
from mutualistes.views import (
    ajouter_beneficiaires, beneficiaire_list, import_beneficiaires, import_mutualistes, mutualiste_list, mutualiste_create, mutualiste_list_actif, mutualiste_list_nonactif, mutualiste_listunique, 
    mutualiste_update, mutualiste_detail, mutualistes_beneficiaires_list, nature_prestation_create, nature_prestation_delete, nature_prestation_list, nature_prestation_update, prestation_sociale_create, prestation_sociale_delete, prestation_sociale_list, prestation_sociale_listsolde, prestation_sociale_listtts, prestation_sociale_traiter, prestation_sociale_update,
    toggle_mutualiste_status
)
from prestations.views import (
    ajouter_dispensation, ajouter_medicament, ajouter_prescription, ajouter_prestations, ajouter_prestations_beneficiaire, ajouter_prestationsex, ajouter_prestationsex_beneficiaire, ajouter_prestationshospi, ajouter_prestationshospibeneficiaire, ajouter_prestationsoptique, ajouter_prestationsoptiquebeneficiaire, demarrer_prise_en_charge, detail_prise_en_charge, detail_prise_en_chargeoptique, importer_medicaments, liste_medicaments, liste_validations, listedetail_prestations, listedetail_prestationspharma, modifier_medicament, prestation_list, prestation_detail, 
    prestation_create, prestation_update,prescription_update,
    prestation_delete,importer_prestations, prestations_par_all, prestations_par_mois, prestations_pdf, supprimer_medicament, telecharger_prise_en_charge_pdf, valider_code_prescription, valider_examen, valider_hospitalisation, valider_matricule, valider_optique
)
from centres.views import (
    ListeCentreSanteView, ajouter_centre_sante, ajouter_centre_sante, ajouter_groupe, ajouter_medecin, centre_sante_delete,
    filtrer_prestations, importer_centres_sante, importer_prestationscentre, liste_centres_actifs, liste_centres_nonactifs, liste_groupes, modifier_groupe, supprimer_groupe, toggle_centre_status
)
from utilisateurs.views import (
    ajouter_utilisateur, liste_utilisateurs, modifier_utilisateur, reinitialiser_mot_de_passe, supprimer_utilisateur
)
# ================================== API 
from configurations.views import (
    LoginView, RegisterView,ProfileView,CentreSanteListCreateView,logout_userbank,HopitalListView,RefreshTokenView,ProfilMutualisteView,PrestationCombinedViewSet,RemboursementListCreateView)

urlpatterns = [
    path("admin/", admin.site.urls),
    #"""path('login/', views.login_view, name='login'),
    
    #path('logout/', logout_view, name='logout'),
    # Ajouter d'autres URL de tableaux de bord selon les rôles
    #path('dashboard_superadmin/', superadmin_dashboard_view, name='dashboard_superadmin'),
    #path('dashboard_admin/', admin_dashboard_view, name='dashboard_admin'),
    #path('dashboard_medecin/', medecin_dashboard_view, name='dashboard_medecin'),
    #path('dashboard_point_focal/', point_focal_dashboard_view, name='dashboard_point_focal'),
    #path('dashboard_pharmacie/', pharmacie_dashboard_view, name='dashboard_pharmacie'),"""
    
# Frontoffice
    # Dashboard
    path('backoffice/tableau_de_bord/', tableau_de_bord, name='tableau_de_bord'),
    path('frontoffice/dashboard_centre_sante/', centre_sante_dashboard_view, name='dashboard_centre_sante'),
    path('frontoffice/dashboard_pharmacie/', tableau_de_bord_pharmacie, name='tableau_de_bord_pharmacie'),
    path("frontoffice/dashboard_medecin/", dashboard_medecin, name="dashboard_medecin"),
    path('frontoffice/dashboard_optique/', optique_dashboard_view, name='dashboard_optique'),
    path('frontoffice/dashboard_point_focal/', dashboard_point_focal, name='dashboard_point_focal'),
    
    path('frontoffice/point_focal/', point_focal, name='point_focal'),
    path('frontoffice/point_focal/mutualiste/', point_focal_mutualiste, name='point_focal_mutualiste'),
    path('frontoffice/point_focal/prestataire/', point_focal_prestataire, name='point_focal_prestataire'),
    path('frontoffice/point_focal/prestations/', point_focal_prestations, name='point_focal_prestations'),
    path('frontoffice/point_focal/dispensations/', point_focal_dispensations, name='point_focal_dispensations'),
    path('frontoffice/point_focal/cotisations/', point_focal_cotisations, name='point_focal_cotisations'),
    path('frontoffice/point_focal/cotisations/<int:cotisation_id>/paiements/', point_focal_paiements, name='point_focal_paiements'),
    
    path('api/prises/', get_prise_en_charge_events, name='prises_en_charge_api'),
    #path('login/', login_view, name='login'),
    path('', login_view, name='login'),
    path('logout/', logout_view, name='signup'),
    
    # Prise en charges
    path('frontoffice/prise-en-charge/', demarrer_prise_en_charge, name='prise_en_charge'),
    path('valider-matricule/', valider_matricule, name='valider_matricule'),
    path('frontoffice/ajouter-prestations/<int:id>/', ajouter_prestations, name='ajouter_prestations'),
    path('frontoffice/ajouter-prestations-beneficiaire/<int:id>/', ajouter_prestations_beneficiaire, name='ajouter_prestations_beneficiaire'),
    path('frontoffice/ajouter_prestationsex/<int:id>/', ajouter_prestationsex, name='ajouter_prestationsex'),
    path('frontoffice/ajouter_prestationsex_beneficiaire/<int:id>/', ajouter_prestationsex_beneficiaire, name='ajouter_prestationsex_beneficiaire'),
    path('frontoffice/ajouter-prestationshospi/<int:id>/', ajouter_prestationshospi, name='ajouter_prestationshospi'),
    path('frontoffice/ajouter-prestationshospi-beneficiaire/<int:id>/', ajouter_prestationshospibeneficiaire, name='ajouter_prestationshospi_beneficiaire'),
    path('frontoffice/validations/', liste_validations, name='liste_validations'),
    path('frontoffice/validations/hospitalisation/<int:id>/', valider_hospitalisation, name='valider_hospitalisation'),
    path('frontoffice/validations/examen/<int:id>/', valider_examen, name='valider_examen'),
    path('frontoffice/detail-prise-en-charge/<int:prise_en_charge_id>/', detail_prise_en_charge, name='detail_prise_en_charge'),
    path("frontoffice/ajouter-medecin/", ajouter_medecin, name="ajouter_medecin"),
    path('frontoffice/prescription/ajouter/<int:id>/', ajouter_prescription, name='ajouter_prescription'),
    path('frontoffice/prescription/<int:pk>/modifier/', prescription_update, name='prescription_update'),
    path('frontoffice/detail-prestations/', listedetail_prestations, name='listedetail_prestations'),
    path('frontoffice/priseencharge/pdf/<int:id>/', telecharger_prise_en_charge_pdf, name='telecharger_prise_en_charge_pdf'),

    
    path('frontoffice/optique/ajouter-prestations/<int:id>/', ajouter_prestationsoptique, name='ajouter_prestationsoptique'),
    path('frontoffice/optique/ajouter-prestations-beneficiaire/<int:id>/', ajouter_prestationsoptiquebeneficiaire, name='ajouter_prestationsoptique_beneficiaire'),
    path('frontoffice/optique/detail-prise-en-charge/<int:prise_en_charge_id>/', detail_prise_en_chargeoptique, name='detail_prise_en_chargeoptique'),
    path('frontoffice/validations/optique/<int:id>/', valider_optique, name='valider_optique'),
    
     #  Facturations
    path("frontoffice/factures/", liste_factures, name="liste_factures"),
    path("frontoffice/facture/<int:facture_id>/", detail_facture, name="detail_facture"),
    path("frontoffice/pharmacie/factures/", liste_facturespharmacie, name="liste_facturespharmacie"),
    path('frontoffice/pharmacie/facture/<int:facture_id>/', detail_facturepharmacie, name='detail_facturepharmacie'),
    
    # Dispensation pharmacie
    path('valider-code_prescription/', valider_code_prescription, name='valider_code_prescription'),
    path('frontoffice/ajouter-dispensation/<int:id>/', ajouter_dispensation, name='ajouter_dispensation'),
    path('frontoffice/detail-prestations/pharma/', listedetail_prestationspharma, name='listedetail_prestationspharma'),
    
# Backoffice
    # Mutualistes
    path('backoffice/mutualiste-beneficiaire', mutualistes_beneficiaires_list, name='mutualistes_beneficiaires_list'),
    path('backoffice/mutualistes-unique', mutualiste_listunique, name='mutualiste_listunique'),
    path('backoffice/mutualistes', mutualiste_list, name='mutualiste_list'),
    path('backoffice/mutualistes/actif', mutualiste_list_actif, name='mutualiste_list_actif'),
    path('backoffice/mutualistes/non-actif', mutualiste_list_nonactif, name='mutualiste_list_nonactif'),
    path('backoffice/mutualistes/create/', mutualiste_create, name='mutualiste_create'),
    path('backoffice/mutualistes/<int:pk>/', mutualiste_detail, name='mutualiste_detail'),
    path('backoffice/mutualistes/<int:pk>/edit/', mutualiste_update, name='mutualiste_update'),
    path('mutualiste/<int:mutualiste_id>/toggle-status/', toggle_mutualiste_status, name='toggle_mutualiste_status'),
    path('backoffice/mutualistes/importer-mutualistes/', import_mutualistes, name='import_mutualistes'),
    
    # Beneficiares
    path('beneficiaires/<int:mutualiste_id>/', ajouter_beneficiaires, name='ajouter_beneficiaires'),
    path('backoffice/beneficiaires', beneficiaire_list, name='beneficiaire_list'),
    path('backoffice/beneficiaires/importer-beneficiaires/', import_beneficiaires, name='import_beneficiaires'),
    
    # Prestations
    path('backoffice/prestations/', prestation_list, name='prestation_list'),
    path('backoffice/prestations/<int:pk>/', prestation_detail, name='prestation_detail'),
    path('backoffice/prestations/ajouter/', prestation_create, name='prestation_create'),
    path('backoffice/prestations/<int:pk>/modifier/', prestation_update, name='prestation_update'),
    path('backoffice/prestations/<int:pk>/supprimer/', prestation_delete, name='prestation_delete'),
    path('backoffice/prestations/importer/', importer_prestations, name='importer_prestations'),
    
    # Facturations
    path("backoffice/factures/impayees/", factures_impayees_anterieures, name="factures_impayees"),
    path("backoffice/factures/payees/", factures_payees_anterieures, name="factures_payees"),
    path("backoffice/factures/impayees/mois/", factures_impayees_encours, name="factures_impayees_encours"),
    path('backoffice/factures/<int:facture_id>/toggle-status/', toggle_factures_status, name='toggle_factures_status'),
    
    # Centre_santes
    path('backoffice/centre_sante/liste/', ListeCentreSanteView.as_view(), name='liste_centre_sante'),
    path('backoffice/centre_sante-actif/liste/', liste_centres_actifs, name='liste_centres_actifs'),
    path('backoffice/centre_sante-non-actif/liste/', liste_centres_nonactifs, name='liste_centres_nonactifs'),
    path('backoffice/centre_sante/ajouter/', ajouter_centre_sante, name='ajouter_centre_sante'),
    path('backoffice/centre_sante/modifier/<int:pk>/', ajouter_centre_sante, name='modifier_centre_sante'),
    path('backoffice/centre_sante/supprimer/<int:pk>/', centre_sante_delete, name='centre_sante_delete'),
    path('filtrer_prestations/', filtrer_prestations, name='filtrer_prestations'),
    path('backoffice/centre_sante/importer-prestations/', importer_prestationscentre, name='importer_prestationscentre'),
    path('backoffice/centre_sante/<int:centre_id>/toggle/', toggle_centre_status, name='toggle_centre_status'),
    path('backoffice/centre_sante/importer-centres-sante/', importer_centres_sante, name='importer_centres_sante'),
    
    # medicaments
    path('backoffice/medicament/', liste_medicaments, name='liste_medicament'),
    path('backoffice/medicament/ajouter/', ajouter_medicament, name='ajouter_medicament'),
    path('backoffice/medicament/modifier/<int:pk>/', modifier_medicament, name='modifier_medicament'),
    path('backoffice/medicament/supprimer/<int:pk>/', supprimer_medicament, name='supprimer_medicament'),
    path('backoffice/medicament/importer/', importer_medicaments, name='importer_medicaments'),  # Route pour importer un fichier Excel
    
    # Nature de Prestation Sociale
    path('backoffice/natures/', nature_prestation_list, name='nature_list'),
    path('backoffice/natures/ajouter/', nature_prestation_create, name='nature_create'),
    path('backoffice/natures/modifier/<int:pk>/', nature_prestation_update, name='nature_update'),
    path('backoffice/natures/supprimer/<int:pk>/', nature_prestation_delete, name='nature_delete'),

    # Prestation Sociale
    path('backoffice/prestations/sociale', prestation_sociale_list, name='prestation_sociale_list'),
    path('backoffice/prestations/sociale/traitees', prestation_sociale_listtts, name='prestation_sociale_listtts'),
    path('backoffice/prestations/sociale/soldees', prestation_sociale_listsolde, name='prestation_sociale_listsolde'),
    path('backoffice/prestations/sociale/<int:pk>/ajouter/', prestation_sociale_create, name='prestation_create_social'),
    path('backoffice/prestations/sociale/modifier/<int:pk>/', prestation_sociale_update, name='prestation_update_social'),
    path('backoffice/prestations/sociale/supprimer/<int:pk>/', prestation_sociale_delete, name='prestation_delete_social'),
    path('backoffice/prestations/sociale/traitement/<int:pk>/', prestation_sociale_traiter, name='prestation_sociale_traiter'),
    
    # Sinistres
    path('backoffice/sinistres/prestations/', prestations_par_mois, name='prestations_par_mois'),
    path('backoffice/sinistres/prestations/pdf/', prestations_pdf, name='prestations_pdf'),
    path('backoffice/sinistres/prestations/all/', prestations_par_all, name='prestations_par_all'),
    
    # Cotisations
    path('backoffice/cotisations/', liste_cotisations, name='liste_cotisations'),
    path('backoffice/cotisations/paiements/<int:cotisation_id>/', liste_paiements, name='liste_paiements'),
    path('backoffice/cotisations/paiement/ajouter/<int:cotisation_id>/', ajouter_paiement, name='ajouter_paiement'),
    path('backoffice/cotisations/paiement/modifier/<int:paiement_id>/', modifier_paiement, name='modifier_paiement'),
    path('backoffice/cotisations/paiement/supprimer/<int:paiement_id>/', supprimer_paiement, name='supprimer_paiement'),
    
    # Groupes
    path('backoffice/groupes/', liste_groupes, name='liste_groupes'),
    path('backoffice/groupes/ajouter/', ajouter_groupe, name='ajouter_groupe'),
    path('backoffice/groupes/modifier/<int:groupe_id>/', modifier_groupe, name='modifier_groupe'),
    path('backoffice/groupes/supprimer/<int:groupe_id>/', supprimer_groupe, name='supprimer_groupe'),
    
    # Utilisateurs
    path('backoffice/utilisateurs/', liste_utilisateurs, name='liste_utilisateurs'),
    path('backoffice/utilisateurs/modifier/<int:user_id>/', modifier_utilisateur, name='modifier_utilisateur'),
    path('backoffice/utilisateurs/supprimer/<int:user_id>/', supprimer_utilisateur, name='supprimer_utilisateur'),
    path('backoffice/utilisateurs/ajouter/', ajouter_utilisateur, name='ajouter_utilisateur'),
    path('backoffice/utilisateurs/reset/<int:user_id>/', reinitialiser_mot_de_passe, name='reinitialiser_mot_de_passe'),

    # Categories
    path('backoffice/categorie/affection', liste_categories, name='categorie_liste'),
    path('backoffice/categorie/affection/ajouter/', ajouter_categorie, name='categorie_ajouter'),
    path('backoffice/categorie/affection/<int:pk>/modifier/', modifier_categorie, name='categorie_modifier'),
    path('backoffice/categorie/affection/<int:pk>/supprimer/', supprimer_categorie, name='categorie_supprimer'),
    
    # codes affections
    path('backoffice/codes/', code_affection_list, name='code_affection_list'),
    path('backoffice/codes/ajouter/', code_affection_create, name='code_affection_create'),
    path('backoffice/codes/modifier/<int:pk>/', code_affection_update, name='code_affection_update'),
    path('backoffice/codes/supprimer/<int:pk>/', code_affection_delete, name='code_affection_delete'),
    
    # ordonnances
    path('backoffice/ordonnances/', ordonnance_list, name='ordonnance_list'),
    path('backoffice/ordonnances/ajouter/', ordonnance_create, name='ordonnance_create'),
    path('backoffice/ordonnances/modifier/<int:pk>/', ordonnance_update, name='ordonnance_update'),
    path('backoffice/ordonnances/supprimer/<int:pk>/', ordonnance_delete, name='ordonnance_delete'),



# ================================== API ============================================================ API ==================================================
    path('loginapi', LoginView.as_view(), name='loginapi'),
    path('logout_userbank', logout_userbank, name='logout_userbank'),
    path('registerapi/', RegisterView.as_view(), name='registerapi'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('token/refresh/', RefreshTokenView.as_view(), name='token_refresh'),  # Rafraîchir le token
    
    # Liste des boutons accueil
    path('centres-santeapi/', CentreSanteListCreateView.as_view(), name='centres-sante-list'),
    path('hopitaux/', HopitalListView.as_view(), name='hopital-list'),
    path('prestations/mutualiste', PrestationCombinedViewSet.as_view(), name='prestationmutualiste'),
    
    path('api/profil-mutualiste/', ProfilMutualisteView.as_view(), name='profil-mutualiste'),
    
    path('api/remboursements/', RemboursementListCreateView.as_view(), name='remboursements-list-create'),
    
    path('api/prestations-sociales/', PrestationSocialeListCreateView.as_view(), name='prestation-sociale-list-create'),
    path('api/natures-prestations-sociales/', liste_natures_prestations_sociales, name='natures-prestations-sociales'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)