import streamlit as st
import datetime
import random
from streamlit_folium import st_folium
import folium
import pandas as pd

# Configuration de la page
st.set_page_config(
    page_title="SentinelleCI",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personnalisé
st.markdown("""
<style>
    /* Supprimer les marges par défaut */
    .main > div {
        padding: 0;
        margin: 0;
    }
    
    /* Bloc vert en haut */
    .green-header {
        background: linear-gradient(135deg, #1a5e2a 0%, #2d8a3e 100%);
        padding: 20px 16px 20px 16px;
        color: white;
        margin: -60px 0 0 0;
    }
    
    .green-header h1 {
        margin: 0;
        font-size: 24px;
        font-weight: 600;
        text-align: center;
        padding-top: 40px;
    }
    
    /* Barre de recherche */
    .search-bar {
        margin-top: 15px;
        margin-bottom: 10px;
    }
    
    .search-bar input {
        width: 100%;
        padding: 12px 16px;
        border: none;
        border-radius: 25px;
        font-size: 14px;
        background: rgba(255,255,255,0.2);
        color: white;
        outline: none;
    }
    
    .search-bar input::placeholder {
        color: rgba(255,255,255,0.7);
    }
    
    /* Bloc blanc pour le contenu */
    .white-content {
        background: white;
        border-radius: 25px 25px 0 0;
        padding: 20px 16px;
        margin-top: -20px;
    }
    
    /* Titre CARTE DES SIGNALEMENTS */
    .section-title {
        font-size: 18px;
        font-weight: 600;
        color: #1a5e2a;
        margin-bottom: 15px;
        text-align: center;
    }
    
    /* Titre avec flèche de retour */
    .section-title-with-back {
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 20px;
    }
    
    .back-arrow {
        font-size: 24px;
        cursor: pointer;
        background: none;
        border: none;
        color: #1a5e2a;
        font-weight: bold;
        transition: transform 0.2s ease;
    }
    
    .back-arrow:hover {
        transform: translateX(-3px);
    }
    
    .section-title-with-back h2 {
        margin: 0;
        font-size: 20px;
        color: #1a5e2a;
        flex: 1;
        text-align: center;
        padding-right: 30px;
    }
    
    /* Indicateurs colorés */
    .stats-indicators {
        display: flex;
        justify-content: space-around;
        margin: 20px 0;
        gap: 10px;
    }
    
    .indicator {
        text-align: center;
        flex: 1;
        background: #f8f9fa;
        border-radius: 12px;
        padding: 10px;
    }
    
    .indicator-color {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        margin: 0 auto 8px auto;
    }
    
    .indicator-number {
        font-size: 20px;
        font-weight: bold;
        margin: 5px 0;
    }
    
    .indicator-label {
        font-size: 11px;
        color: #6c757d;
    }
    
    /* Cartes statistiques doubles */
    .stats-double {
        display: flex;
        gap: 15px;
        margin: 20px 0;
    }
    
    .stat-card-half {
        flex: 1;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 15px;
        padding: 15px;
        text-align: center;
    }
    
    .stat-card-half .number {
        font-size: 28px;
        font-weight: bold;
        color: #1a5e2a;
    }
    
    .stat-card-half .label {
        font-size: 12px;
        color: #6c757d;
        margin-top: 5px;
    }
    
    /* Bouton flottant vert avec + */
    .floating-button {
        position: fixed;
        bottom: 80px;
        right: 20px;
        width: 56px;
        height: 56px;
        background: linear-gradient(135deg, #28a745 0%, #1a5e2a 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
        z-index: 1000;
        border: none;
    }
    
    .floating-button:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 16px rgba(0,0,0,0.4);
    }
    
    .floating-button span {
        font-size: 32px;
        font-weight: bold;
        color: white;
    }
    
    /* Navigation du bas */
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        display: flex;
        justify-content: space-around;
        padding: 12px 16px;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
        border-radius: 20px 20px 0 0;
        z-index: 100;
    }
    
    .nav-item {
        text-align: center;
        cursor: pointer;
        flex: 1;
        padding: 5px;
        transition: all 0.3s ease;
    }
    
    .nav-item:hover {
        transform: translateY(-2px);
    }
    
    .nav-icon {
        font-size: 22px;
        display: block;
    }
    
    .nav-label {
        font-size: 11px;
        color: #6c757d;
        margin-top: 4px;
    }
    
    .nav-active .nav-label {
        color: #2d8a3e;
        font-weight: 600;
    }
    
    /* Marge pour ne pas cacher le contenu */
    .content-bottom-padding {
        padding-bottom: 80px;
    }
    
    /* Formulaire de signalement */
    .form-section {
        background: #f8f9fa;
        border-radius: 15px;
        padding: 16px;
        margin-bottom: 16px;
    }
    
    .form-section-title {
        font-size: 14px;
        font-weight: 600;
        color: #333;
        margin-bottom: 12px;
    }
    
    .photo-buttons {
        display: flex;
        gap: 12px;
    }
    
    .photo-btn {
        flex: 1;
        background: #e9ecef;
        border: none;
        padding: 12px;
        border-radius: 10px;
        font-size: 13px;
        cursor: pointer;
        text-align: center;
        transition: background 0.3s ease;
    }
    
    .photo-btn:hover {
        background: #dee2e6;
    }
    
    .location-info {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .location-text {
        flex: 1;
    }
    
    .location-badge {
        background: #d4edda;
        color: #155724;
        padding: 4px 8px;
        border-radius: 20px;
        font-size: 11px;
        display: inline-block;
        margin-bottom: 8px;
    }
    
    .problem-types {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
    }
    
    .problem-type-btn {
        background: #f8f9fa;
        border: 2px solid #e9ecef;
        padding: 12px;
        border-radius: 10px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .problem-type-btn.selected {
        background: #d4edda;
        border-color: #28a745;
        color: #155724;
    }
    
    .submit-btn {
        width: 100%;
        background: linear-gradient(135deg, #28a745 0%, #1a5e2a 100%);
        color: white;
        border: none;
        padding: 14px;
        border-radius: 25px;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        margin-top: 20px;
        transition: transform 0.3s ease;
    }
    
    .submit-btn:hover {
        transform: translateY(-2px);
    }
    
    /* Checkbox personnalisée */
    .checkbox-container {
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 16px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation des données
if 'signalements' not in st.session_state:
    st.session_state.signalements = [
        {'id': 'SIG-001', 'type': 'Route', 'quartier': 'Azito', 'lat': 5.3415, 'lng': -4.0142, 'statut': 'en_attente', 'date': datetime.datetime.now() - datetime.timedelta(days=2)},
        {'id': 'SIG-002', 'type': 'Éclairage', 'quartier': 'Maroc', 'lat': 5.3591, 'lng': -4.0195, 'statut': 'en_cours', 'date': datetime.datetime.now() - datetime.timedelta(days=5)},
        {'id': 'SIG-003', 'type': 'Eau', 'quartier': 'Sicogi', 'lat': 5.3856, 'lng': -3.9974, 'statut': 'resolu', 'date': datetime.datetime.now() - datetime.timedelta(days=10)},
        {'id': 'SIG-004', 'type': 'Route', 'quartier': 'Yopougon', 'lat': 5.3225, 'lng': -4.0552, 'statut': 'en_attente', 'date': datetime.datetime.now() - datetime.timedelta(days=1)},
        {'id': 'SIG-005', 'type': 'École', 'quartier': 'Niagon', 'lat': 5.3591, 'lng': -4.0195, 'statut': 'en_cours', 'date': datetime.datetime.now() - datetime.timedelta(days=3)},
    ]

if 'page' not in st.session_state:
    st.session_state.page = 'accueil'
if 'selected_type' not in st.session_state:
    st.session_state.selected_type = None

# Fonction pour créer la carte
def create_map():
    m = folium.Map(location=[5.3415, -4.0142], zoom_start=11, control_scale=True)
    
    colors = {
        'en_attente': 'red',
        'en_cours': 'orange',
        'resolu': 'green'
    }
    
    for s in st.session_state.signalements:
        color = colors.get(s['statut'], 'gray')
        
        popup_html = f"""
        <div style="font-family: sans-serif; min-width: 150px;">
            <h4 style="margin: 0 0 5px 0;">{s['type']}</h4>
            <p style="margin: 2px 0;"><strong>Quartier:</strong> {s['quartier']}</p>
            <p style="margin: 2px 0;"><strong>ID:</strong> {s['id']}</p>
        </div>
        """
        
        folium.Marker(
            location=[s['lat'], s['lng']],
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color=color, icon='info-sign')
        ).add_to(m)
    
    return m

# Calcul des statistiques
def get_stats():
    total = len(st.session_state.signalements)
    en_attente = len([s for s in st.session_state.signalements if s['statut'] == 'en_attente'])
    en_cours = len([s for s in st.session_state.signalements if s['statut'] == 'en_cours'])
    resolus = len([s for s in st.session_state.signalements if s['statut'] == 'resolu'])
    
    return {
        'total': total,
        'en_attente': en_attente,
        'en_cours': en_cours,
        'resolus': resolus,
        'resolus_mois': 45,
        'delai_moyen': 12
    }

# ==================== AFFICHAGE ====================

# HEADER VERT
st.markdown("""
<div class="green-header">
    <h1>📍 Sentinelle.CI</h1>
    <div class="search-bar">
        <input type="text" placeholder="Rechercher un quartier, une adresse..." id="search-input">
    </div>
</div>
""", unsafe_allow_html=True)

# CONTENU BLANC
st.markdown('<div class="white-content">', unsafe_allow_html=True)

# PAGE ACCUEIL
if st.session_state.page == 'accueil':
    stats = get_stats()
    
    st.markdown('<div class="section-title">🗺️ CARTE DES SIGNALEMENTS</div>', unsafe_allow_html=True)
    
    m = create_map()
    st_data = st_folium(m, width=800, height=400, returned_objects=[])
    
    st.markdown(f"""
    <div class="stats-indicators">
        <div class="indicator">
            <div class="indicator-color" style="background: #dc3545;"></div>
            <div class="indicator-number" style="color: #dc3545;">{stats['en_attente']}</div>
            <div class="indicator-label">Problèmes signalés</div>
        </div>
        <div class="indicator">
            <div class="indicator-color" style="background: #fd7e14;"></div>
            <div class="indicator-number" style="color: #fd7e14;">{stats['en_cours']}</div>
            <div class="indicator-label">En cours</div>
        </div>
        <div class="indicator">
            <div class="indicator-color" style="background: #28a745;"></div>
            <div class="indicator-number" style="color: #28a745;">{stats['resolus']}</div>
            <div class="indicator-label">Résolus</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="stats-double">
        <div class="stat-card-half">
            <div class="number">45</div>
            <div class="label">Signalements validés</div>
        </div>
        <div class="stat-card-half">
            <div class="number">{stats['delai_moyen']} jours</div>
            <div class="label">Délai moyen</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# PAGE NOUVEAU SIGNALEMENT
elif st.session_state.page == 'nouveau_signalement':
    # Titre avec flèche de retour
    col_back, col_title = st.columns([1, 8])
    with col_back:
        if st.button("←", key="back_btn"):
            st.session_state.page = 'accueil'
            st.rerun()
    with col_title:
        st.markdown('<h2 style="color: #1a5e2a; margin: 0;">Nouveau signalement</h2>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Formulaire
    with st.form("signalement_form", clear_on_submit=False):
        # PHOTO DU PROBLÈME
        st.markdown('<div class="form-section-title">📸 PHOTO DU PROBLÈME</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div style="background: #e9ecef; padding: 10px; border-radius: 10px; text-align: center;">📷 PRENDRE UNE PHOTO</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div style="background: #e9ecef; padding: 10px; border-radius: 10px; text-align: center;">🖼️ CHOISIR DANS LA GALERIE</div>', unsafe_allow_html=True)
        
        photo = st.file_uploader("", type=['jpg', 'jpeg', 'png'], label_visibility="collapsed")
        
        st.markdown("---")
        
        # LOCALISATION
        st.markdown('<div class="form-section-title">📍 LOCALISATION</div>', unsafe_allow_html=True)
        st.markdown('<div class="location-badge">✓ Géolocalisation activée</div>', unsafe_allow_html=True)
        
        # Mini carte pour la localisation
        location_map = folium.Map(location=[5.3415, -4.0142], zoom_start=13, control_scale=True)
        folium.Marker([5.3415, -4.0142], icon=folium.Icon(color='blue', icon='circle', prefix='fa')).add_to(location_map)
        st_folium(location_map, width=400, height=200, returned_objects=[])
        
        st.markdown("---")
        
        
        # TYPE DE PROBLÈME
        st.markdown('<div class="form-section-title">🔄 TYPE DE PROBLÈME</div>', unsafe_allow_html=True)

        # Utilisation d'un selectbox (ou radio) à la place des st.button
        type_probleme = st.selectbox(
            "",
            options=["Route", "Eau", "École", "Éclairage"],
            index=None,
            placeholder="Choisissez le type de problème...",
            label_visibility="collapsed"
        )
        if type_probleme:
            st.session_state.selected_type = type_probleme
            st.info(f"Sélectionné: {st.session_state.selected_type}")

            st.markdown("---")

        
        # DESCRIPTION
        st.markdown('<div class="form-section-title">📝 DESCRIPTION (optionnelle)</div>', unsafe_allow_html=True)
        description = st.text_area("", placeholder="Décrivez le problème...", height=100, label_visibility="collapsed")
        
        st.markdown("---")
        
        # ACCEPTATION BLOCKCHAIN
        accept = st.checkbox("✅ J'accepte la publication sur blockchain (immuable)")
        
        # BOUTON SIGNALER
        submitted = st.form_submit_button("SIGNALER SUR BLOCKCHAIN", use_container_width=True)
        
        if submitted and accept and st.session_state.selected_type:
            new_id = f"SIG-{len(st.session_state.signalements) + 1:03d}"
            st.session_state.signalements.append({
                'id': new_id,
                'type': st.session_state.selected_type,
                'quartier': "Nouveau quartier",
                'date': datetime.datetime.now(),
                'statut': 'en_attente',
                'lat': 5.3415 + random.uniform(-0.05, 0.05),
                'lng': -4.0142 + random.uniform(-0.05, 0.05),
                'description': description
            })
            st.success(f"✅ Signalement {new_id} envoyé avec succès sur la blockchain !")
            st.balloons()
            retour = st.form_submit_button("🏠 Retour à l'accueil")
            if retour:
                st.session_state.page = 'accueil'
                st.rerun()
        elif submitted and not accept:
            st.error("Veuillez accepter la publication sur blockchain")
        elif submitted and not st.session_state.selected_type:
            st.error("Veuillez sélectionner un type de problème")

# PAGE MES SIGNALEMENTS
elif st.session_state.page == 'mes_signalements':
    st.markdown('<div class="section-title">📋 Mes signalements</div>', unsafe_allow_html=True)
    
    mes_signalements = st.session_state.signalements[-5:]
    
    if mes_signalements:
        for s in reversed(mes_signalements):
            status_color = {
                'en_attente': ('🔴 En attente', '#dc3545'),
                'en_cours': ('🟠 En cours', '#fd7e14'),
                'resolu': ('🟢 Résolu', '#28a745')
            }.get(s['statut'], ('⚪ Inconnu', '#6c757d'))
            
            st.markdown(f"""
            <div style="background: #f8f9fa; border-radius: 12px; padding: 12px; margin-bottom: 10px; border-left: 4px solid {status_color[1]};">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <strong>{s['type']}</strong>
                    <span style="font-size: 11px; color: #999;">{s['date'].strftime('%d/%m/%Y')}</span>
                </div>
                <div style="font-size: 13px; color: #666;">ID: {s['id']}</div>
                <div style="font-size: 11px; margin-top: 5px; color: {status_color[1]};">{status_color[0]}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("📭 Vous n'avez pas encore de signalements")

# PAGE PROFIL
elif st.session_state.page == 'profil':
    st.markdown('<div class="section-title">👤 Mon profil</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 20px;">
            <div style="font-size: 60px;">👤</div>
            <h3 style="margin: 10px 0 5px 0;">Citoyen</h3>
            <p style="color: #6c757d;">Membre depuis avril 2026</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### 📊 Mes statistiques")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Mes signalements", "5")
    with col2:
        st.metric("Résolus", "2")
    
    st.markdown("### ⚙️ Préférences")
    st.checkbox("Notifications", value=True)
    st.selectbox("Langue", ["Français", "English"])

st.markdown('</div>', unsafe_allow_html=True)

# BOUTON FLOUTANT VERT AVEC + (uniquement sur la page accueil)
if st.session_state.page == 'accueil':
    st.markdown("""
    <div class="floating-button" id="float-btn">
        <span>+</span>
    </div>
    <script>
        document.getElementById('float-btn').addEventListener('click', function() {
            // Redirection via Streamlit
            const streamlitDebug = parent.window.parent;
            // Utiliser un callback pour changer la page
            parent.postMessage({type: "streamlit:setComponentValue", value: "nouveau_signalement"}, "*");
        });
    </script>
    """, unsafe_allow_html=True)

# Bouton flottant alternatif avec Streamlit (plus fiable)
if st.session_state.page == 'accueil':
    # Utiliser un espace pour positionner le bouton
    st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)

# NAVIGATION FIXE EN BAS
st.markdown("""
<div class="bottom-nav">
    <div class="nav-item" data-nav="accueil">
        <span class="nav-icon">🏠</span>
        <span class="nav-label">Accueil</span>
    </div>
    <div class="nav-item" data-nav="mes_signalements">
        <span class="nav-icon">📋</span>
        <span class="nav-label">Mes signalements</span>
    </div>
    <div class="nav-item" data-nav="profil">
        <span class="nav-icon">👤</span>
        <span class="nav-label">Profil</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Navigation alternative avec boutons Streamlit
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🏠 Accueil", use_container_width=True):
        st.session_state.page = 'accueil'
        st.rerun()
with col2:
    if st.button("📋 Mes signalements", use_container_width=True):
        st.session_state.page = 'mes_signalements'
        st.rerun()
with col3:
    if st.button("👤 Profil", use_container_width=True):
        st.session_state.page = 'profil'
        st.rerun()

# Bouton flottant + (alternative fiable)
if st.session_state.page == 'accueil':
    st.markdown("---")
    if st.button("➕ NOUVEAU SIGNALEMENT", use_container_width=True):
        st.session_state.page = 'nouveau_signalement'
        st.rerun()

st.markdown('<div style="padding-bottom: 60px;"></div>', unsafe_allow_html=True)