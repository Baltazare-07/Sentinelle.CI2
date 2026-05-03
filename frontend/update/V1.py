import streamlit as st
import datetime
import random
from streamlit_folium import st_folium
import folium
import requests

# Configuration de la page
st.set_page_config(
    page_title="SentinelleCI",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialisation des données de démonstration
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

# Fonction pour créer la carte avec liens Etherscan
def create_map():
    m = folium.Map(location=[5.3415, -4.0142], zoom_start=11)
    colors = {'en_attente': 'red', 'en_cours': 'orange', 'resolu': 'green'}
    
    for s in st.session_state.signalements:
        if s.get('tx_hash') and s['tx_hash'].startswith('0x'):
            etherscan_url = f"https://sepolia.etherscan.io/tx/{s['tx_hash']}"
            short_id = s['id'][:20] + '...' if len(s['id']) > 20 else s['id']
            popup_html = f"""
            <div style="font-family: sans-serif; min-width: 200px;">
                <b>{s['type']}</b><br>
                📍 {s['quartier']}<br>
                🆔 {short_id}<br>
                🔗 <a href='{etherscan_url}' target='_blank'>Voir sur Etherscan</a>
            </div>
            """
        else:
            popup_html = f"{s['type']} - {s['quartier']}"
        
        folium.Marker(
            location=[s['lat'], s['lng']],
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color=colors.get(s['statut'], 'gray'))
        ).add_to(m)
    return m

# HEADER
st.markdown('<div style="background: linear-gradient(135deg, #1a5e2a 0%, #2d8a3e 100%); padding: 20px; color: white; text-align: center;"><h1>📍 Sentinelle.CI</h1></div>', unsafe_allow_html=True)

# PAGE ACCUEIL
if st.session_state.page == 'accueil':
    st.markdown("## 🗺️ CARTE DES SIGNALEMENTS")
    m = create_map()
    st_folium(m, width=800, height=400)
    
    # Statistiques
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Problèmes signalés", len([s for s in st.session_state.signalements if s['statut'] == 'en_attente']))
    with col2:
        st.metric("En cours", len([s for s in st.session_state.signalements if s['statut'] == 'en_cours']))
    with col3:
        st.metric("Résolus", len([s for s in st.session_state.signalements if s['statut'] == 'resolu']))
    
    # Derniers signalements
    st.markdown("## 📋 Derniers signalements")
    for s in reversed(st.session_state.signalements[-5:]):
        col1, col2, col3 = st.columns([3, 2, 2])
        with col1:
            st.write(f"**{s['type']}** - {s['quartier']}")
        with col2:
            date_str = s['date'].strftime('%d/%m/%Y') if isinstance(s['date'], datetime.datetime) else s['date'][:10]
            st.write(f"📅 {date_str}")
        with col3:
            if s.get('tx_hash') and s['tx_hash'].startswith('0x'):
                etherscan_url = f"https://sepolia.etherscan.io/tx/{s['tx_hash']}"
                st.markdown(f"[🔍 Voir sur Etherscan]({etherscan_url})")
            else:
                st.write(f"🆔 {s['id'][:16]}...")
        st.divider()
    
    if st.button("➕ NOUVEAU SIGNALEMENT", use_container_width=True):
        st.session_state.page = 'nouveau_signalement'
        st.rerun()

# PAGE NOUVEAU SIGNALEMENT
elif st.session_state.page == 'nouveau_signalement':
    st.markdown("## Nouveau signalement")
    
    if st.button("← Retour"):
        st.session_state.page = 'accueil'
        st.rerun()
    
    st.markdown("---")
    
    # Type de problème
    type_probleme = st.selectbox(
        "Type de problème",
        ["Route", "Eau", "École", "Éclairage"],
        index=None,
        placeholder="Choisissez..."
    )
    if type_probleme:
        st.session_state.selected_type = type_probleme
        st.info(f"Sélectionné: {type_probleme}")
    
    # Description
    description = st.text_area("Description (optionnelle)", placeholder="Décrivez le problème...")
    
    # Acceptation
    accept = st.checkbox("✅ J'accepte la publication sur blockchain (immuable)")
    
    # Bouton de soumission
    if st.button("SIGNALER SUR BLOCKCHAIN", use_container_width=True):
        if not accept:
            st.error("Veuillez accepter la publication sur blockchain")
        elif not st.session_state.selected_type:
            st.error("Veuillez sélectionner un type de problème")
        else:
            # Préparation des données
            signalement_data = {
                'type': st.session_state.selected_type,
                'description': description,
                'quartier': "Nouveau quartier",
                'latitude': 5.3415 + random.uniform(-0.05, 0.05),
                'longitude': -4.0142 + random.uniform(-0.05, 0.05)
            }
            
            try:
                with st.spinner("⏳ Enregistrement sur la blockchain en cours..."):
                    response = requests.post(
                        'http://localhost:3001/api/signalements',
                        json=signalement_data,
                        timeout=10
                    )
                    
                    if response.status_code in [200, 201]:
                        result = response.json()
                        new_id = result.get('id')
                        tx_hash = result.get('tx_hash')
                        blockchain_url = result.get('blockchain_url')
                        
                        # Ajout local avec le hash blockchain
                        st.session_state.signalements.append({
                            'id': new_id,
                            'type': st.session_state.selected_type,
                            'quartier': "Nouveau quartier",
                            'date': datetime.datetime.now(),
                            'statut': 'en_attente',
                            'lat': signalement_data['latitude'],
                            'lng': signalement_data['longitude'],
                            'description': description,
                            'tx_hash': tx_hash,
                            'blockchain_url': blockchain_url
                        })
                        
                        st.success(f"✅ Signalement enregistré avec succès sur la blockchain !")
                        short_hash = tx_hash[:20] + '...' if len(tx_hash) > 20 else tx_hash
                        st.markdown(f"🔗 **Hash transaction:** `{short_hash}`")
                        if blockchain_url:
                            st.markdown(f"[🔍 **Vérifier sur Etherscan**]({blockchain_url})")
                        st.balloons()
                        
                        # Retour à l'accueil
                        st.session_state.page = 'accueil'
                        st.session_state.selected_type = None
                        st.rerun()
                    else:
                        st.error(f"❌ Erreur: {response.status_code}")
                        
            except requests.exceptions.ConnectionError:
                st.error("❌ Impossible de se connecter au backend. Vérifiez que le serveur tourne sur le port 3001")
            except Exception as e:
                st.error(f"❌ Erreur: {str(e)}")

# PAGE MES SIGNALEMENTS
elif st.session_state.page == 'mes_signalements':
    st.markdown("## 📋 Mes signalements")
    
    if st.button("← Retour"):
        st.session_state.page = 'accueil'
        st.rerun()
    
    st.markdown("---")
    
    mes_signalements = st.session_state.signalements[-10:]
    for s in reversed(mes_signalements):
        with st.container():
            # Statut avec couleur
            if s['statut'] == 'resolu':
                status_emoji = "🟢"
                status_text = "Résolu"
            elif s['statut'] == 'en_cours':
                status_emoji = "🟠"
                status_text = "En cours"
            else:
                status_emoji = "🔴"
                status_text = "En attente"
            
            # Afficher les informations
            short_id = s['id'][:24] + '...' if len(s['id']) > 24 else s['id']
            date_str = s['date'].strftime('%d/%m/%Y') if isinstance(s['date'], datetime.datetime) else s['date'][:10]
            
            st.markdown(f"""
            **{s['type']}** - `{short_id}`  
            📍 {s['quartier']} - {date_str}  
            {status_emoji} {status_text}
            """)
            
            # Ajouter le lien Etherscan si disponible
            if s.get('tx_hash') and s['tx_hash'].startswith('0x'):
                etherscan_url = f"https://sepolia.etherscan.io/tx/{s['tx_hash']}"
                st.markdown(f"🔗 [🔍 **Vérifier sur Etherscan**]({etherscan_url})")
            
            st.divider()

# PAGE PROFIL
elif st.session_state.page == 'profil':
    st.markdown("## 👤 Mon profil")
    
    if st.button("← Retour"):
        st.session_state.page = 'accueil'
        st.rerun()
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 👤 Citoyen")
        st.markdown("Membre depuis avril 2026")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Mes signalements", len(st.session_state.signalements))
    with col2:
        st.metric("Résolus", len([s for s in st.session_state.signalements if s['statut'] == 'resolu']))
    
    st.markdown("### ⚙️ Préférences")
    st.checkbox("Notifications", value=True)
    st.selectbox("Langue", ["Français", "English"])

# Navigation en bas
st.markdown("---")
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