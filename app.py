import streamlit as st
import geopandas as gpd
import folium as flm
from streamlit_folium import st_folium
import pandas as pd
from datetime import datetime 


# Configuration de la page Streamlit
st.set_page_config(page_title="Gestion des Alertes - Sicap Liberté", layout="wide")

st.title("Alerte - Inondations & Regards Bouchés")
st.markdown("**Zone d'étude : Sicap Liberté, Dakar** — Signalez en temps réel les dysfonctionnements du réseau à l'ONAS.")

# --- 1. CHARGEMENT DES DONNÉES (Simulé ici, gardez vos variables geopandas) ---
@st.cache_data
def charger_donnees():
    commune = gpd.read_file('data/Commune_sicap_liberté.shp').to_crs(epsg=4326)
    bati =  gpd.read_file('data/Batit_.shp').to_crs(epsg=4326)
    regard =  gpd.read_file('data/Regards.shp').to_crs(epsg=4326)
    return commune, bati, regard

commune, bati, regard = charger_donnees()

# --- 2. CRÉATION DE LA CARTE INTERACTIVE ---
def generer_carte():
    carte = flm.Map(location=[14.7199648, -17.483976], zoom_start=15, tiles="CartoDB positron")
    flm.TileLayer('Esri WorldImagery', name='Vue Satellite').add_to(carte)
    
    # Vos styles
    style_commune = lambda x: {'fillColor': 'transparent', 'color': 'yellow', 'weight': 5, 'dashArray': '5, 5'}
    style_bati = lambda x: {'fillColor': 'gray', 'color': '#e74c3c', 'weight': 1, 'fillOpacity': 0.4}
    #style_eaupliue = lambda x: {'color': 'Blue', 'weight': 4, 'opacity': 0.6}
    #style_eauuse = lambda x: {'color': 'red', 'weight': 4, 'opacity': 0.6}
    
    # Ajout des couches (Vérifiez que vos variables GeoJSON sont chargées)
    flm.GeoJson(commune, name="Commune", style_function=style_commune).add_to(carte)
    flm.GeoJson(bati, name="Bati", style_function=style_bati).add_to(carte)
    
    # Couches des Regards
    flm.GeoJson(
    regard,
    name="Regards",
    marker=flm.CircleMarker(radius=10, color="#8e44ad", fill_color="#2c3e50", fill_opacity=0.9),
    popup=flm.GeoJsonPopup(fields=['NUMERO', 'Typer']),
    tooltip=flm.GeoJsonTooltip(fields=['NUMERO', 'Typer']) ).add_to(carte)

    
    flm.LayerControl(collapsed=False).add_to(carte)
    return carte

# --- 3. MISE EN PAGE DE L'APPLICATION (COLONNES) ---
col1, col2 = st.columns([2, 1]) # La carte prend 2/3 de l'écran, le formulaire 1/3

with col1:
    st.subheader("Carte du Réseau d'Assainissement")
    # Affichage de la carte Folium dans Streamlit
    # st_folium permet de capturer les clics de l'utilisateur sur la carte
    carte_folium = generer_carte()
    donnees_carte = st_folium(carte_folium, width=800, height=550)

with col2:
    st.subheader("Urgence (ONAS)")
    
    # Formulaire de saisie
    with st.form(key="formulaire_alerte", clear_on_submit=True):
        nom_citoyen = st.text_input("Votre Nom / Prénom (Optionnel)")
        telephone = st.text_input("Numéro de Téléphone (Pour suivi ONAS) *")
        
        # Sélection du regard concerné
        numero_regard = st.text_input("Numéro du Regard défectueux *", 
                                      help="Regardez sur la carte et cliquez sur le point pour obtenir son NUMERO.")
        
        type_probleme = st.selectbox(
            "Type de problème constaté *",
            ["Regard bouché par les ordures", "Débordement d'eaux usées", "Inondation de chaussée (Eau pluviale)", "Plaque de regard cassée/manquante"]
        )
        
        gravite = st.select_slider("Niveau d'urgence *", options=["Faible", "Moyen", "Critique"])
        commentaire = st.text_area("Précisions importantes (Ex: Devant la boulangerie...)")
        
        bouton_envoi = st.form_submit_button(label="Envoyer")
        
        # Traitement de l'envoi
        if bouton_envoi:
            if not telephone or not numero_regard:
                st.error("❌ Veuillez remplir les champs obligatoires (*)")
            else:
                # Création de l'objet Alerte
                nouvelle_alerte = {
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Citoyen": nom_citoyen,
                    "Telephone": telephone,
                    "Regard_ID": numero_regard,
                    "Type": type_probleme,
                    "Gravite": gravite,
                    "Commentaire": commentaire,
                    "Statut": "En attente de traitement"
                }
                
                # Écriture dans un fichier de sauvegarde (Base de données simplifiée en CSV)
                try:
                    df_existante = pd.read_csv("alertes_onas.csv")
                    df_nouvelle = pd.DataFrame([nouvelle_alerte])
                    df_finale = pd.concat([df_existante, df_nouvelle], ignore_index=True)
                    df_finale.to_csv("alertes_onas.csv", index=False)
                except FileNotFoundError:
                    df_finale = pd.DataFrame([nouvelle_alerte])
                    df_finale.to_csv("alertes_onas.csv", index=False)
                
                st.success(f"✅ Alerte enregistrée avec succès pour le regard N° {numero_regard} ! Transmis à l'équipe technique ONAS.")

# --- 4. ESPACE SUIVI DES ALERTES (POUR LES AGENTS DE L'ONAS) ---
st.write("---")
st.subheader("Tableau de bord des signalements Vue ONAS)")
try:
    df_alertes = pd.read_csv("alertes_onas.csv")
    st.dataframe(df_alertes.style.set_properties(**{'background-color': '#f9f9f9'}))
except FileNotFoundError:
    st.info("Aucune alerte n'a été émise pour le moment.")