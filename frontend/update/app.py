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
    initial_sidebar_state="expanded"
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
if 'show_prise_en_charge' not in st.session_state:
    st.session_state.show_prise_en_charge = False

# ==================== SIDEBAR ====================
with st.sidebar:
    st.image("https://via.placeholder.com/150x80?text=Sentinelle.CI", use_container_width=False)
    st.markdown("## 📍 Sentinelle.CI")
    st.markdown("---")
    
    # Navigation principale
    st.markdown("### 📱 Navigation")
    if st.button("🏠 Accueil", use_container_width=True):
        st.session_state.page = 'accueil'
        st.rerun()
    
    if st.button("📋 Mes signalements", use_container_width=True):
        st.session_state.page = 'mes_signalements'
        st.rerun()
    
    if st.button("👤 Mon profil", use_container_width=True):
        st.session_state.page = 'profil'
        st.rerun()
    
    st.markdown("---")
    
    # Espace Administration
    st.markdown("### 👑 Administration")
    if st.button("🏛️ Vue Mairie", use_container_width=True, type="primary"):
        st.session_state.page = 'mairie'
        st.rerun()
    
    st.markdown("---")
    
    # Informations
    st.markdown("### ℹ️ À propos")
    st.info("""
    **Sentinelle.CI**  
    Plateforme citoyenne de signalement  
    des travaux publics
    
    Version 1.0 | Blockchain Ready
    """)
    
    st.markdown("---")
    
    # Statistiques rapides
    st.markdown("### 📊 Stats rapides")
    total = len(st.session_state.signalements)
    en_attente = len([s for s in st.session_state.signalements if s['statut'] == 'en_attente'])
    st.metric("Total signalements", total)
    st.metric("En attente", en_attente)

# ==================== FONCTIONS ====================

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

# ==================== PAGES ====================

# HEADER (supprimé car la sidebar est plus propre)
st.markdown('<div style="padding: 0px;"></div>', unsafe_allow_html=True)

# PAGE ACCUEIL
if st.session_state.page == 'accueil':
    st.markdown("## 🗺️ CARTE DES SIGNALEMENTS")
    m = create_map()
    st_folium(m, width=800, height=400)
    
    # Statistiques
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("⚠️ Problèmes signalés", len([s for s in st.session_state.signalements if s['statut'] == 'en_attente']))
    with col2:
        st.metric("🔄 En cours", len([s for s in st.session_state.signalements if s['statut'] == 'en_cours']))
    with col3:
        st.metric("✅ Résolus", len([s for s in st.session_state.signalements if s['statut'] == 'resolu']))
    
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
    
    mes_signalements = st.session_state.signalements[-10:]
    if not mes_signalements:
        st.info("📭 Vous n'avez pas encore de signalements")
    else:
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
    
    if st.button("➕ NOUVEAU SIGNALEMENT", use_container_width=True):
        st.session_state.page = 'nouveau_signalement'
        st.rerun()

# PAGE PROFIL
elif st.session_state.page == 'profil':
    st.markdown("## 👤 Mon profil")
    
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

# PAGE TABLEAU DE BORD MAIRIE
elif st.session_state.page == 'mairie':
    st.markdown("## 📊 TABLEAU DE BORD COMMUNAL")
    st.markdown(f"**Mise à jour : {datetime.datetime.now().strftime('%H:%M:%S')}**")
    st.markdown("---")
    
    # Calcul des stats
    total = len(st.session_state.signalements)
    en_attente = len([s for s in st.session_state.signalements if s['statut'] == 'en_attente'])
    en_cours = len([s for s in st.session_state.signalements if s['statut'] == 'en_cours'])
    resolus = len([s for s in st.session_state.signalements if s['statut'] == 'resolu'])
    
    # Indicateurs clés
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📋 En attente", en_attente, delta="+5 depuis hier", delta_color="inverse")
    with col2:
        st.metric("🚧 En cours", en_cours, delta="2 interventions aujourd'hui")
    with col3:
        st.metric("✅ Résolus ce mois", resolus, delta="+12 vs mois dernier")
    with col4:
        delai_moyen = 12
        st.metric("⏱️ Délai moyen", f"{delai_moyen} jours", delta="Objectif: <15 jours")
    
    st.markdown("---")
    
    # Deux colonnes principales
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.markdown("### 🚨 SIGNALEMENTS NON PRIS EN CHARGE")
        non_pris = [s for s in st.session_state.signalements if s['statut'] == 'en_attente']
        
        if non_pris:
            for i, s in enumerate(non_pris):
                date_str = s['date'].strftime('%d/%m/%Y') if isinstance(s['date'], datetime.datetime) else s['date'][:10]
                signalement_id = f"SIG-ABJ-2026-{str(i+1).zfill(3)}"
                
                col_id, col_type, col_quartier, col_date, col_action = st.columns([1.5, 1, 1, 1, 1])
                with col_id:
                    st.write(f"**{signalement_id}**")
                with col_type:
                    st.write(s['type'])
                with col_quartier:
                    st.write(s['quartier'])
                with col_date:
                    st.write(date_str)
                with col_action:
                    if st.button("📋 PRENDRE", key=f"prendre_mairie_{i}"):
                        st.session_state.selected_signalement = s
                        st.session_state.show_prise_en_charge = True
                        st.rerun()
                st.divider()
        else:
            st.info("✅ Aucun signalement en attente")
    
    with col_right:
        st.markdown("### 📊 RÉPARTITION")
        total = len(st.session_state.signalements)
        if total > 0:
            st.markdown(f"""
            **Total:** {total}  
            - 🔴 En attente: {en_attente} ({en_attente/total*100:.1f}%)  
            - 🟠 En cours: {en_cours} ({en_cours/total*100:.1f}%)  
            - 🟢 Résolus: {resolus} ({resolus/total*100:.1f}%)
            """)
            
            # Barre de progression
            st.progress(en_attente/total, text="Taux de résolution")
        
        st.markdown("---")
        st.markdown("### 👥 Agents terrain")
        st.markdown("""
        - 👤 Koffi A. (3 interventions)
        - 👤 Diallo M. (2 interventions)
        - 👤 Kouadio L. (1 intervention)
        """)
    
    # Section Prise en charge
    if st.session_state.show_prise_en_charge and st.session_state.get('selected_signalement'):
        st.markdown("---")
        st.markdown("## 📋 PRISE EN CHARGE D'UN SIGNALEMENT")
        
        s = st.session_state.selected_signalement
        date_str = s['date'].strftime('%d/%m/%Y à %H:%M') if isinstance(s['date'], datetime.datetime) else s['date'][:10]
        
        col_left2, col_right2 = st.columns(2)
        with col_left2:
            st.info(f"""
            **Signalement #{s['id'][:16]}...**  
            📍 {s['type']} - {s['quartier']}  
            📅 Signalé le {date_str}
            """)
        
        with col_right2:
            agent = st.selectbox("**Assigner à**", ["Koffi A.", "Diallo M.", "Kouadio L.", "Yao B."])
            commentaire = st.text_area("**Commentaire public**", placeholder="Ex: Intervention programmée...")
            date_intervention = st.date_input("**Date intervention prévue**", datetime.datetime.now() + datetime.timedelta(days=7))
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("✅ VALIDER", use_container_width=True):
                    for signalement in st.session_state.signalements:
                        if signalement['id'] == s['id']:
                            signalement['statut'] = 'en_cours'
                            signalement['agent'] = agent
                            break
                    st.session_state.show_prise_en_charge = False
                    st.success(f"✅ Signalement assigné à {agent}")
                    st.rerun()
            with col_btn2:
                if st.button("❌ ANNULER", use_container_width=True):
                    st.session_state.show_prise_en_charge = False
                    st.rerun()

# Navigation dans le contenu principal (optionnel)
st.markdown("---")
st.caption(f"© 2026 Sentinelle.CI - Plateforme citoyenne | Connected to Blockchain")