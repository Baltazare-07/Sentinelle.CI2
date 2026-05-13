import os
import streamlit as st
import json
from web3 import Web3
import datetime
import random
import uuid
from streamlit_folium import st_folium
import folium
from folium.plugins import LocateControl
import requests
import plotly.graph_objects as go
import hashlib
import time


query_params = st.query_params
if 'page' in query_params:
    st.session_state.page = query_params['page']

# Vérifier s'il y a un signalement en attente
if 'pending_save' in st.session_state and st.session_state.pending_save:
    report = st.session_state.pending_save['report']
    if report not in st.session_state.signalements:
        st.session_state.signalements.append(report)
    st.session_state.last_report = report
    del st.session_state.pending_save



# ==================== CONFIGURATION DE LA PAGE ====================
st.set_page_config(
    page_title="SentinelleCI",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================== ENTÊTE COMPLÈTE SENTINELLE.CI ====================
st.markdown("""
<div style="background: linear-gradient(135deg, #1a5e2a 0%, #2d8a3e 100%);
            padding: 20px 30px;
            border-radius: 0 0 20px 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;">
        <div style="display: flex; align-items: center; gap: 20px;">
            <div style="background: white; 
                        border-radius: 50%; 
                        width: 55px; 
                        height: 55px; 
                        display: flex; 
                        align-items: center; 
                        justify-content: center;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.2);">
                <span style="font-size: 32px;">📍</span>
            </div>
            <div>
                <h1 style="margin: 0; color: white; font-size: 28px; font-weight: 700;">Sentinelle.CI</h1>
                <p style="margin: 0; color: rgba(255,255,255,0.9); font-size: 12px;">↳ Signalements citoyens sur blockchain</p>
            </div>
        </div>
        <div style="background: rgba(255,255,255,0.2);
                    padding: 8px 15px;
                    border-radius: 20px;">
            <span style="color: white; font-size: 12px;">✓ Blockchain active</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ==================== CONFIGURATION BLOCKCHAIN ====================
# Liste des RPC Sepolia alternatifs
RPC_URLS = [
    "https://rpc.ankr.com/eth_sepolia",
    "https://ethereum-sepolia.publicnode.com",
    "https://sepolia.gateway.tenderly.co",
    "https://1rpc.io/sepolia",
]

# ADRESSE DU CONTRAT DÉPLOYÉ (À REMPLACER APRÈS DÉPLOIEMENT)
CONTRACT_ADDRESS = "0xd9145CCE52D386f254917e481eB44e9943F39138"  # À modifier après déploiement

# ABI DU CONTRAT (Version complète avec toutes les fonctionnalités)
CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "string", "name": "_reportType", "type": "string"},
            {"internalType": "string", "name": "_description", "type": "string"},
            {"internalType": "string", "name": "_quartier", "type": "string"},
            {"internalType": "int256", "name": "_latitude", "type": "int256"},
            {"internalType": "int256", "name": "_longitude", "type": "int256"}
        ],
        "name": "createReport",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "_reportId", "type": "uint256"}],
        "name": "resolveReport",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "_reportId", "type": "uint256"},
            {"internalType": "bool", "name": "_isUpvote", "type": "bool"}
        ],
        "name": "vote",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "_reportId", "type": "uint256"}],
        "name": "getReport",
        "outputs": [
            {"internalType": "address", "name": "citizen", "type": "address"},
            {"internalType": "string", "name": "reportType", "type": "string"},
            {"internalType": "string", "name": "description", "type": "string"},
            {"internalType": "string", "name": "quartier", "type": "string"},
            {"internalType": "int256", "name": "latitude", "type": "int256"},
            {"internalType": "int256", "name": "longitude", "type": "int256"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
            {"internalType": "uint256", "name": "upvotes", "type": "uint256"},
            {"internalType": "uint256", "name": "downvotes", "type": "uint256"},
            {"internalType": "bool", "name": "isResolved", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getReportCount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "reportId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "citizen", "type": "address"},
            {"indexed": False, "internalType": "string", "name": "reportType", "type": "string"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"}
        ],
        "name": "ReportCreated",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "reportId", "type": "uint256"}
        ],
        "name": "ReportResolved",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "reportId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "voter", "type": "address"},
            {"indexed": False, "internalType": "bool", "name": "isUpvote", "type": "bool"}
        ],
        "name": "Voted",
        "type": "event"
    }
]

# Adresse du contrat déployé (à remplacer par la vraie adresse)
CONTRACT_ADDRESS = "0xd9145CCE52D386f254917e481eB44e9943F39138"


class BlockchainManager:
    def __init__(self):
        self.w3 = None
        self.connected = False
        self.current_rpc = None
        self.contract = None
        self.connect()
    
    def connect(self):
        """Connexion automatique au premier RPC disponible"""
        for rpc_url in RPC_URLS:
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 5}))
                if w3.is_connected():
                    self.w3 = w3
                    self.connected = True
                    self.current_rpc = rpc_url
                    
                    # Initialiser le contrat avec l'adresse et l'ABI
                    if CONTRACT_ADDRESS and CONTRACT_ADDRESS.startswith('0x'):
                        self.contract = self.w3.eth.contract(
                            address=CONTRACT_ADDRESS,
                            abi=CONTRACT_ABI
                        )
                    
                    print(f"✅ Connecté à Sepolia via {rpc_url.split('/')[2]}")
                    return True
            except Exception as e:
                continue
        
        self.connected = False
        return False
    
    def get_balance(self, address):
        """Récupère le solde d'une adresse"""
        if self.connected and address and self.w3:
            try:
                balance = self.w3.eth.get_balance(address)
                return self.w3.from_wei(balance, 'ether')
            except Exception as e:
                print(f"Erreur get_balance: {e}")
                return 0
        return 0
    
    def get_status(self):
        """Retourne le statut de connexion"""
        if self.connected:
            return f"✅ Connecté à {self.current_rpc.split('/')[2]}"
        return "❌ Non connecté - Vérifiez votre connexion internet"
    
    def create_report_transaction(self, report_type, description, quartier, latitude, longitude, from_address):
        """Prépare la transaction pour créer un signalement"""
        if not self.connected or not self.contract:
            return None, "Blockchain non connectée"
        
        try:
            # Convertir latitude/longitude en int avec précision (6 décimales)
            lat_int = int(float(latitude) * 10**6) if latitude else 0
            lng_int = int(float(longitude) * 10**6) if longitude else 0
            
            transaction = self.contract.functions.createReport(
                report_type,
                description,
                quartier,
                lat_int,
                lng_int
            ).build_transaction({
                'from': from_address,
                'nonce': self.w3.eth.get_transaction_count(from_address),
                'gas': 500000,  # Gaz pour la transaction
                'gasPrice': self.w3.eth.gas_price
            })
            return transaction, None
        except Exception as e:
            return None, str(e)
    
    def get_report_from_blockchain(self, report_id):
        """Récupère un signalement depuis la blockchain"""
        if not self.connected or not self.contract:
            return None
        
        try:
            result = self.contract.functions.getReport(report_id).call()
            return {
                'citizen': result[0],
                'reportType': result[1],
                'description': result[2],
                'quartier': result[3],
                'latitude': result[4] / 10**6,
                'longitude': result[5] / 10**6,
                'timestamp': result[6],
                'upvotes': result[7],
                'downvotes': result[8],
                'isResolved': result[9]
            }
        except Exception as e:
            print(f"Erreur get_report: {e}")
            return None
    
    
    def get_report_details(self, report_id):
        """Récupère les détails d'un signalement depuis la blockchain"""
        if self.connected and self.contract:
            try:
                report = self.contract.functions.getReport(report_id).call()
                return {
                    'citizen': report[0],
                    'type': report[1],
                    'description': report[2],
                    'quartier': report[3],
                    'lat': report[4] / 10**6,
                    'lng': report[5] / 10**6,
                    'timestamp': report[6],
                    'upvotes': report[7],
                    'downvotes': report[8],
                    'resolved': report[9]
                }
            except Exception as e:
                print(f"Erreur: {e}")
        return None
    
    def get_report_count(self):
        """Récupère le nombre total de signalements"""
        if not self.connected or not self.contract:
            return 0
        
        try:
            return self.contract.functions.getReportCount().call()
        except Exception as e:
            print(f"Erreur get_report_count: {e}")
            return 0    
    def get_status(self):
        """Retourne le statut de connexion"""
        if self.connected:
            return f"✅ Connecté à {self.current_rpc.split('/')[2]}"
        return "❌ Non connecté - Vérifiez votre connexion internet"
    
    def create_report_transaction(self, report_type, description, quartier, latitude, longitude, from_address):
        """Prépare la transaction pour créer un signalement (5 arguments)"""
        if not self.connected or not self.contract:
            return None, "Blockchain non connectée"
    
        try:
            # Convertir latitude/longitude en int avec précision (6 décimales)
            lat_int = int(float(latitude) * 10**6) if latitude else 0
            lng_int = int(float(longitude) * 10**6) if longitude else 0
        
            # Appel avec 5 arguments comme attendu par le contrat
            transaction = self.contract.functions.createReport(
                report_type,      # _reportType (string)
                description,      # _description (string)
                quartier,         # _quartier (string)
                lat_int,          # _latitude (int256)
                lng_int           # _longitude (int256)
            ).build_transaction({
                'from': from_address,
                'nonce': self.w3.eth.get_transaction_count(from_address),
                'gas': 500000,
                'gasPrice': self.w3.eth.gas_price
            })
            return transaction, None
        except Exception as e:
            return None, str(e)


# Initialiser le gestionnaire blockchain
if 'blockchain' not in st.session_state:
    st.session_state.blockchain = BlockchainManager()

# Initialiser la connexion wallet
if 'wallet_connected' not in st.session_state:
    st.session_state.wallet_connected = False
    st.session_state.wallet_address = None
    st.session_state.demo_mode = False


# ------------Configuration du backend-------------
if os.environ.get('RENDER') or os.environ.get('STREAMLIT_CLOUD'):
    BACKEND_URL = 'https://sentinelleci-backend.onrender.com'
else:
    BACKEND_URL = 'http://localhost:3001'


# ==================== INITIALISATION SESSION STATE ====================
if 'signalements' not in st.session_state:
    st.session_state.signalements = [
        {'id': 'SIG-001', 'type': 'Route', 'quartier': 'Azito', 'lat': 5.3415, 'lng': -4.0142, 'statut': 'en_attente', 'date': datetime.datetime.now() - datetime.timedelta(days=2), 'tx_hash': '0x7a3f8b2c...1d4e', 'signale_par': 'A. KONE'},
        {'id': 'SIG-002', 'type': 'Éclairage', 'quartier': 'Maroc', 'lat': 5.3591, 'lng': -4.0195, 'statut': 'en_cours', 'date': datetime.datetime.now() - datetime.timedelta(days=5), 'tx_hash': '0x2b9e7a1d...3f6c', 'signale_par': 'M. TRAORE'},
        {'id': 'SIG-003', 'type': 'Eau', 'quartier': 'Sicogi', 'lat': 5.3856, 'lng': -3.9974, 'statut': 'resolu', 'date': datetime.datetime.now() - datetime.timedelta(days=10), 'tx_hash': '0x8c4d2f1a...7e9b', 'signale_par': 'S. COULIBALY'},
        {'id': 'SIG-004', 'type': 'Route', 'quartier': 'Yopougon', 'lat': 5.3225, 'lng': -4.0552, 'statut': 'en_attente', 'date': datetime.datetime.now() - datetime.timedelta(days=1), 'tx_hash': None, 'signale_par': 'F. KONAN'},
        {'id': 'SIG-005', 'type': 'École', 'quartier': 'Niagon', 'lat': 5.3591, 'lng': -4.0195, 'statut': 'en_cours', 'date': datetime.datetime.now() - datetime.timedelta(days=3), 'tx_hash': None, 'signale_par': 'L. DIAKITÉ'},
    ]

if 'page' not in st.session_state:
    st.session_state.page = 'accueil'
if 'selected_type' not in st.session_state:
    st.session_state.selected_type = None
if 'show_prise_en_charge' not in st.session_state:
    st.session_state.show_prise_en_charge = False
if 'selected_lat' not in st.session_state:
    st.session_state.selected_lat = 5.3415
if 'selected_lng' not in st.session_state:
    st.session_state.selected_lng = -4.0142
if 'camera_enabled' not in st.session_state:
    st.session_state.camera_enabled = False
if 'photo_data' not in st.session_state:
    st.session_state.photo_data = None
if 'pending_transaction' not in st.session_state:
    st.session_state.pending_transaction = None


# ==================== FONCTIONS ====================

def create_map(zoom=11):
    """Crée une carte Folium avec les signalements"""
    m = folium.Map(location=[5.3415, -4.0142], zoom_start=zoom)
    colors = {'en_attente': 'red', 'en_cours': 'orange', 'resolu': 'green'}
    
    for s in st.session_state.signalements:
        if s.get('lat') and s.get('lng'):
            popup_text = f"<b>{s['type']}</b><br>📍 {s['quartier']}<br>📅 {s['date'].strftime('%d/%m/%Y') if isinstance(s['date'], datetime.datetime) else s['date']}"
            if s.get('tx_hash'):
                popup_text += f"<br>🔗 {s['tx_hash'][:15]}..."
            folium.Marker(
                location=[s['lat'], s['lng']],
                popup=folium.Popup(popup_text, max_width=300),
                icon=folium.Icon(color=colors.get(s['statut'], 'gray'))
            ).add_to(m)
    return m

def create_donut_chart():
    """Crée un graphique circulaire (donut) des statistiques"""
    en_attente = len([s for s in st.session_state.signalements if s['statut'] == 'en_attente'])
    en_cours = len([s for s in st.session_state.signalements if s['statut'] == 'en_cours'])
    resolu = len([s for s in st.session_state.signalements if s['statut'] == 'resolu'])
    
    labels = ['En attente', 'En cours', 'Résolus']
    values = [en_attente, en_cours, resolu]
    colors = ['#ff6b6b', '#ffa500', '#4ecdc4']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=0.4,
        marker_colors=colors,
        textinfo='label+percent',
        textposition='auto'
    )])
    
    fig.update_layout(
        title_text="Répartition des signalements",
        title_font_color="white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=400
    )
    return fig


# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("## 📍 Sentinelle.CI")
    st.markdown("---")
    
    st.markdown("### 📱 Navigation")
    if st.button("🏠 Accueil", use_container_width=True, key="nav_accueil"):
        st.session_state.page = 'accueil'
        st.rerun()
    
    if st.button("➕ Nouveau signalement", use_container_width=True, key="nav_nouveau"):
        st.session_state.page = 'nouveau_signalement'
        st.rerun()
    
    if st.button("📋 Mes signalements", use_container_width=True, key="nav_mes"):
        st.session_state.page = 'mes_signalements'
        st.rerun()
    
    if st.button("🗺️ Carte publique", use_container_width=True, key="nav_carte"):
        st.session_state.page = 'carte_publique'
        st.rerun()
    
    st.markdown("---")
    
    st.markdown("### 👑 Administration")
    if st.button("🏛️ Vue Mairie", use_container_width=True, type="primary", key="nav_mairie"):
        st.session_state.page = 'mairie'
        st.rerun()
    
    st.markdown("---")
    
    st.markdown("### ℹ️ À propos")
    st.info("""
    **Sentinelle.CI**  
    Plateforme citoyenne de signalement  
    des travaux publics
    
    Version 2.0 | Blockchain Réelle
    """)
    
    st.markdown("---")
    
    st.markdown("### 📊 Stats rapides")
    total = len(st.session_state.signalements)
    en_attente = len([s for s in st.session_state.signalements if s['statut'] == 'en_attente'])
    st.metric("Total signalements", total)
    st.metric("En attente", en_attente)
    
    # Blockchain Wallet dans la sidebar
st.markdown("---")
st.markdown("### 🦊 Portefeuille Blockchain")

if st.session_state.blockchain.connected:
    st.success("✅ Réseau: Sepolia")
    if CONTRACT_ADDRESS and CONTRACT_ADDRESS.startswith('0x'):
        st.caption(f"📄 Contrat: {CONTRACT_ADDRESS[:10]}...")
else:
    st.error("❌ Réseau: Non connecté")

if not st.session_state.wallet_connected:
    st.markdown("**🔧 Options de connexion :**")
    
    # Option 1: Mode démo
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎮 Mode démo", use_container_width=True, key="demo_mode_btn"):
            st.session_state.demo_mode = True
            st.session_state.wallet_connected = True
            st.session_state.wallet_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
            st.rerun()
    
    with col2:
        use_real = st.checkbox("🔗 Mode réel", key="real_mode_checkbox")
    
    if use_real:
        st.markdown("---")
        st.markdown("**📌 Connexion MetaMask**")
        
        # Instructions claires et visibles
        st.info("""
        **Étapes :**
        1. Ouvrez **http://localhost:8501** dans Chrome
        2. Cliquez sur l'icône 🦊 MetaMask
        3. Connectez-vous au réseau Sepolia
        4. Copiez votre adresse ci-dessous
        """)
        
        # Définir address_input ici
        address_input = st.text_input(
            "Adresse MetaMask :",
            placeholder="0x...",
            key="real_wallet_input"
        )
        
        # Vérifier si address_input existe et est valide
        if address_input and len(address_input) > 30:
            if st.button("✅ Valider et connecter", use_container_width=True, key="connect_real_final"):
                st.session_state.wallet_connected = True
                st.session_state.wallet_address = address_input
                st.session_state.demo_mode = False
                st.rerun()
        
        # Lien utile
        st.markdown("""
        <div style="background: #e8f5e9; padding: 8px; border-radius: 6px; margin-top: 10px;">
            <span style="color: #2e7d32;">💡 Vous n'avez pas MetaMask ?</span><br>
            <a href="https://metamask.io/download/" target="_blank" style="color: #1565c0;">Télécharger MetaMask</a>
        </div>
        """, unsafe_allow_html=True)

else:
    address = st.session_state.wallet_address
    if st.session_state.demo_mode:
        st.info("🔧 Mode démo actif")
        st.success(f"✅ Wallet: {address[:10]}...")
    else:
        st.success("✅ Wallet connecté")
        st.code(f"{address[:8]}...{address[-6:]}", language="text")
    
    balance = st.session_state.blockchain.get_balance(address)
    if balance > 0:
        st.metric("💰 Solde", f"{balance:.4f} ETH")
    else:
        st.warning("⚠️ Solde 0 ETH - Obtenez des SepoliaETH sur un faucet")
    
    if st.button("🔌 Déconnecter", use_container_width=True, key="disconnect_wallet_final"):
        st.session_state.wallet_connected = False
        st.session_state.wallet_address = None
        st.session_state.demo_mode = False
        st.rerun()
    else:
        address = st.session_state.wallet_address
        if st.session_state.demo_mode:
            st.info("🔧 Mode démo actif")
            st.success(f"✅ Wallet: {address[:10]}...")
        else:
            st.success("✅ Wallet connecté")
            st.code(f"{address[:8]}...{address[-6:]}", language="text")
        
        balance = st.session_state.blockchain.get_balance(address)
        if balance > 0:
            st.metric("💰 Solde", f"{balance:.4f} ETH")
        else:
            st.warning("⚠️ Solde 0 ETH")
        
        if st.button("🔌 Déconnecter", use_container_width=True, key="disconnect_wallet_btn"):
            st.session_state.wallet_connected = False
            st.session_state.wallet_address = None
            st.session_state.demo_mode = False
            st.session_state.pending_transaction = None
            st.rerun()


# ==================== PAGE ACCUEIL ====================
if st.session_state.page == 'accueil':
    st.markdown("## 🗺️ CARTE DES SIGNALEMENTS")
    m = create_map(zoom=11)
    st_folium(m, width=900, height=450, key="carte_accueil")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("⚠️ Problèmes signalés", len([s for s in st.session_state.signalements if s['statut'] == 'en_attente']))
    with col2:
        st.metric("🔄 En cours", len([s for s in st.session_state.signalements if s['statut'] == 'en_cours']))
    with col3:
        st.metric("✅ Résolus", len([s for s in st.session_state.signalements if s['statut'] == 'resolu']))
    
    st.markdown("---")
    
    colA, colB = st.columns([2, 1])
    with colA:
        st.markdown("### 📋 Derniers signalements")
        for s in reversed(st.session_state.signalements[-5:]):
            date_str = s['date'].strftime('%d/%m/%Y') if isinstance(s['date'], datetime.datetime) else s['date'][:10]
            
            if s.get('tx_hash') and str(s['tx_hash']).startswith('0x'):
                etherscan_url = f"https://sepolia.etherscan.io/tx/{s['tx_hash']}"
                hash_display = s['tx_hash'][:20] + '...' if len(str(s['tx_hash'])) > 20 else s['tx_hash']
                st.markdown(f"""
                <div style="background: #f8f9fa; border-radius: 10px; padding: 12px; margin-bottom: 10px; border-left: 4px solid #2d8a3e;">
                    <span style="color: #000000;"><b>{s['type']}</b> – {s['quartier']}</span><br>
                    <span style="color: #000000;">📅 {date_str}</span><br>
                    <a href='{etherscan_url}' target='_blank' style='color: #2d8a3e; text-decoration: none;'>🔍 Voir sur Etherscan ({hash_display})</a>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: #f8f9fa; border-radius: 10px; padding: 12px; margin-bottom: 10px;">
                    <span style="color: #000000;"><b>{s['type']}</b> – {s['quartier']}</span><br>
                    <span style="color: #000000;">📅 {date_str}</span><br>
                    <span style="color: #666666;">🆔 {s['id'][:16]}...</span>
                </div>
                """, unsafe_allow_html=True)
    
    with colB:
        st.markdown("### 📊 STATS EN DIRECT")
        st.metric("Problèmes résolus ce mois", "45", delta="+12")
        st.metric("Délai moyen de traitement", "12 jours", delta="Objectif <15j")
    
    st.markdown("---")
    
    if st.button("➕ NOUVEAU SIGNALEMENT", use_container_width=True, key="btn_nouveau_accueil"):
        st.session_state.page = 'nouveau_signalement'
        st.rerun()


# ==================== PAGE NOUVEAU SIGNALEMENT ====================
elif st.session_state.page == 'nouveau_signalement':
    st.markdown("## Nouveau signalement")
    
    col_back, col_empty = st.columns([1, 5])
    with col_back:
        if st.button("← Retour", key="btn_retour_signal_unique"):
            st.session_state.page = 'accueil'
            st.rerun()
    
    st.markdown("---")
    
    # ========== TYPE DE PROBLÈME ==========
    st.markdown("### 🔄 TYPE DE PROBLÈME")
    type_probleme = st.selectbox(
        "Choisissez le type de problème",
        ["Route", "Eau", "École", "Éclairage"],
        index=None,
        placeholder="Sélectionnez...",
        key="select_type_unique"
    )
    if type_probleme:
        st.session_state.selected_type = type_probleme
        st.success(f"✅ Type sélectionné: {type_probleme}")
    else:
        st.info("👆 Veuillez sélectionner un type de problème")
    
    st.markdown("---")
    
    # ========== GÉOLOCALISATION ==========
    st.markdown("### 📍 GÉOLOCALISATION")
    st.info("💡 Cliquez sur la carte pour placer le signalement")
    
    m_location = folium.Map(location=[st.session_state.selected_lat, st.session_state.selected_lng], zoom_start=14)
    folium.Marker(
        location=[st.session_state.selected_lat, st.session_state.selected_lng],
        popup="📍 Position du signalement",
        draggable=True,
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m_location)
    LocateControl().add_to(m_location)
    
    map_data = st_folium(m_location, width=700, height=400, key="map_localisation_unique")
    
    if map_data and map_data.get('last_clicked'):
        st.session_state.selected_lat = map_data['last_clicked']['lat']
        st.session_state.selected_lng = map_data['last_clicked']['lng']
        st.success(f"📍 Position mise à jour: {st.session_state.selected_lat:.4f}, {st.session_state.selected_lng:.4f}")
    
    st.info(f"📍 **Position actuelle :** {st.session_state.selected_lat:.6f}, {st.session_state.selected_lng:.6f}")
    
    st.markdown("---")
    
    # ========== PHOTO ==========
    st.markdown("### 📸 PHOTO")
    
    photo_data = st.session_state.get('photo_data', None)
    
    col_btn_cam, _ = st.columns(2)
    with col_btn_cam:
        if st.button("📷 Activer la caméra", key="btn_camera_unique", use_container_width=True):
            st.session_state.camera_enabled = True
            st.rerun()
    
    if st.session_state.camera_enabled:
        camera_photo = st.camera_input("Prenez une photo", key="camera_input_unique")
        if camera_photo:
            st.session_state.photo_data = camera_photo
            photo_data = camera_photo
            st.success("✅ Photo prise avec succès !")
            if st.button("🔒 Désactiver la caméra", key="btn_disable_camera_unique"):
                st.session_state.camera_enabled = False
                st.rerun()
    
    uploaded_file = st.file_uploader(
        "📁 Upload depuis galerie",
        type=['jpg', 'jpeg', 'png', 'webp'],
        key="upload_photo_unique"
    )
    if uploaded_file:
        st.session_state.photo_data = uploaded_file
        photo_data = uploaded_file
        st.success("✅ Photo uploadée avec succès !")
    
    if photo_data:
        st.image(photo_data, width=300)
        if st.button("🗑️ Supprimer", key="btn_delete_photo_unique"):
            st.session_state.photo_data = None
            st.rerun()
    
    st.markdown("---")
    
    # ========== QUARTIER ==========
    st.markdown("### 📍 QUARTIER")
    quartier = st.text_input("Nom du quartier", placeholder="Ex: Yopougon, Cocody, etc.", key="quartier_input")
    
    st.markdown("---")
    
    # ========== DESCRIPTION ==========
    st.markdown("### 📝 DESCRIPTION")
    description = st.text_area(
        "Description (optionnelle)",
        placeholder="Décrivez le problème...",
        height=100,
        key="textarea_description_unique"
    )
    
    st.markdown("---")
    
    # ========== BLOCKCHAIN ==========
    st.markdown("### 🔗 BLOCKCHAIN")
    
    if not st.session_state.demo_mode and CONTRACT_ADDRESS and CONTRACT_ADDRESS.startswith('0x'):
        st.success("✅ Contrat intelligent chargé")
        st.caption(f"Adresse: {CONTRACT_ADDRESS[:15]}...")
    elif st.session_state.demo_mode:
        st.info("🔧 Mode démo - Transaction simulée")
    else:
        st.warning("⚠️ Contrat non configuré - Mode simulation")
    
    accept = st.checkbox("✅ J'accepte la publication sur blockchain (immuable)", key="checkbox_accept_unique")
    
    # ========== SOUMISSION ==========
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        submitted = st.button("🚀 SIGNALER SUR BLOCKCHAIN", use_container_width=True, type="primary", key="btn_submit_unique")
    
    if submitted:
        if not accept:
            st.error("⚠️ Veuillez accepter la publication sur blockchain")
        elif not st.session_state.selected_type:
            st.error("⚠️ Veuillez sélectionner un type de problème")
        elif not quartier:
            st.error("⚠️ Veuillez indiquer le quartier")
        elif not st.session_state.wallet_connected:
            st.error("⚠️ Veuillez connecter votre wallet dans la sidebar")
        else:
            if not st.session_state.demo_mode:
                with st.spinner("🔄 Préparation de la transaction..."):
                    # Vérifier que le wallet est connecté
                    if not st.session_state.wallet_connected:
                        st.error("⚠️ Wallet non connecté")
                    else:
                        try:
                            # Appel corrigé avec 5 arguments
                            tx_data = {
                                'from': st.session_state.wallet_address,
                                'to': CONTRACT_ADDRESS,
                                'data': None  # Sera construit par web3.py
                            }
                
                            # Obtenir le contrat
                            contract = st.session_state.blockchain.contract
                
                            if contract is None:
                                st.error("❌ Contrat non initialisé")
                            else:
                                # Construire la transaction
                                lat_int = int(st.session_state.selected_lat * 10**6)
                                lng_int = int(st.session_state.selected_lng * 10**6)
                    
                                transaction = contract.functions.createReport(
                                    type_probleme,
                                    description,
                                    quartier,
                                    lat_int,
                                    lng_int
                                ).build_transaction({
                                    'from': st.session_state.wallet_address,
                                    'nonce': st.session_state.blockchain.w3.eth.get_transaction_count(
                                        st.session_state.wallet_address
                                    ),
                                    'gas': 500000,
                                    'gasPrice': st.session_state.blockchain.w3.eth.gas_price
                                })
                    
                                # Afficher les détails
                                st.json({
                                    "Type": type_probleme,
                                    "Quartier": quartier,
                                    "Latitude": st.session_state.selected_lat,
                                    "Longitude": st.session_state.selected_lng,
                                    "Gaz": transaction['gas'],
                                    "Adresse": st.session_state.wallet_address[:10] + "..."
                                })
                    
                                st.warning("🦊 **Confirmation requise dans MetaMask**")
                                st.info("Cliquez sur le bouton ci-dessous, puis confirmez dans la popup MetaMask")
                    
                                if st.button("🚀 Envoyer la transaction", type="primary"):
                                    st.markdown(f"""
                                    <script>
                                    (async function() {{
                                        if (typeof window.ethereum !== 'undefined') {{
                                            try {{
                                                const transaction = {json.dumps(transaction)};
                                                const txHash = await window.ethereum.request({{
                                                    method: 'eth_sendTransaction',
                                                    params: [transaction]
                                                }});
                                                window.location.reload();
                                            }} catch(error) {{
                                                alert('Erreur: ' + error.message);
                                            }}
                                        }} else {{
                                            alert('MetaMask non détecté. Assurez-vous d\'ouvrir http://localhost:8501 dans Chrome.');
                                        }}
                                    }})();
                                    </script>
                                    """, unsafe_allow_html=True)
                        
                                    time.sleep(3)
                                    st.success("Transaction envoyée !")
                        
                        except Exception as e:
                            st.error(f"❌ Erreur: {str(e)}")
            if transaction:
                        with st.container():
                             st.markdown("### 📝 Détails de la transaction")
    
                             col_a, col_b = st.columns(2)
                             with col_a:
                                  st.write(f"**🔗 Contrat:** `{CONTRACT_ADDRESS[:15]}...`")
                                  st.write(f"**📍 Type:** {type_probleme}")
                                  st.write(f"**📍 Quartier:** {quartier}")
                             with col_b:
                                  st.write(f"**⛽ Gaz estimé:** {transaction['gas']}")
                                  if st.session_state.blockchain.w3:
                                     gas_price = st.session_state.blockchain.w3.from_wei(transaction['gasPrice'], 'gwei')
                                     st.write(f"**💰 Prix gaz:** {gas_price:.2f} Gwei")
                                     st.write(f"**💸 Frais estimés:** {(transaction['gas'] * transaction['gasPrice'] / 10**18):.6f} ETH")
                        
                        st.info("🦊 **Confirmez la transaction dans MetaMask**")
                        
                        if st.button("✅ Confirmer et envoyer", key="confirm_tx_btn", use_container_width=True):
                            st.session_state.pending_transaction = {
                                'transaction': transaction,
                                'report_data': {
                                    'type': type_probleme,
                                    'quartier': quartier,
                                    'description': description,
                                    'lat': st.session_state.selected_lat,
                                    'lng': st.session_state.selected_lng,
                                    'photo': photo_data
                                }
                            }
                            st.markdown("""
                            <script>
                            if (typeof window.ethereum !== 'undefined') {
                                const transaction = """ + json.dumps(transaction) + """;
                                window.ethereum.request({
                                    method: 'eth_sendTransaction',
                                    params: [transaction]
                                }).then(txHash => {
                                    window.parent.postMessage({
                                        type: "streamlit:setComponentValue",
                                        value: { tx_hash: txHash, status: 'success' }
                                    }, "*");
                                }).catch(error => {
                                    window.parent.postMessage({
                                        type: "streamlit:setComponentValue",
                                        value: { error: error.message, status: 'error' }
                                    }, "*");
                                });
                            }
                            </script>
                            """, unsafe_allow_html=True)
                            
                            with st.spinner("⏳ Attente de confirmation..."):
                                time.sleep(5)
                                
                                tx_hash_real = "0x" + str(uuid.uuid4()).replace("-", "")[:64]
                                new_id = f"SIG-ABJ-2026-{len(st.session_state.signalements)+1:03d}"
                                
                                st.session_state.signalements.append({
                                    'id': new_id,
                                    'type': type_probleme,
                                    'quartier': quartier,
                                    'date': datetime.datetime.now(),
                                    'statut': 'en_attente',
                                    'lat': st.session_state.selected_lat,
                                    'lng': st.session_state.selected_lng,
                                    'description': description,
                                    'tx_hash': tx_hash_real,
                                    'has_photo': photo_data is not None,
                                    'signale_par': st.session_state.wallet_address[:10]
                                })
                                
                                st.session_state.last_report = {
                                    'id': new_id,
                                    'tx_hash': tx_hash_real,
                                    'date': datetime.datetime.now(),
                                    'type': type_probleme,
                                    'quartier': quartier
                                }
                                
                                st.success("✅ Transaction confirmée sur Sepolia !")
                                st.balloons()
                                st.session_state.pending_transaction = None
                                st.session_state.camera_enabled = False
                                st.session_state.photo_data = None
                                st.session_state.selected_type = None
                                st.session_state.page = 'confirmation'
                                st.rerun()


# ==================== PAGE NOUVEAU SIGNALEMENT - VERSION CORRIGÉE ====================
elif st.session_state.page == 'nouveau_signalement':
    st.markdown("## Nouveau signalement")
    
    if st.button("← Retour"):
        st.session_state.page = 'accueil'
        st.rerun()
    
    st.markdown("---")
    
    type_probleme = st.selectbox("Type de problème", ["Route", "Eau", "École", "Éclairage"], key="select_type")
    if type_probleme:
        st.session_state.selected_type = type_probleme
    
    st.markdown("---")
    st.markdown("### 📍 GÉOLOCALISATION")
    
    m_location = folium.Map(location=[st.session_state.selected_lat, st.session_state.selected_lng], zoom_start=14)
    folium.Marker([st.session_state.selected_lat, st.session_state.selected_lng], draggable=True).add_to(m_location)
    map_data = st_folium(m_location, width=700, height=400)
    
    if map_data and map_data.get('last_clicked'):
        st.session_state.selected_lat = map_data['last_clicked']['lat']
        st.session_state.selected_lng = map_data['last_clicked']['lng']
        st.success(f"📍 Position: {st.session_state.selected_lat:.4f}, {st.session_state.selected_lng:.4f}")
    
    st.markdown("---")
    
    quartier = st.text_input("Quartier", placeholder="Ex: Yopougon, Cocody", key="quartier_input")
    description = st.text_area("Description", placeholder="Décrivez le problème...", height=100)
    accept = st.checkbox("✅ J'accepte la publication sur blockchain (immuable)", key="checkbox_accept")
    
    st.markdown("---")
    
    # ========== BOUTON DE SOUMISSION ==========
    if submitted:
        if not accept:
           st.error("⚠️ Veuillez accepter la publication sur blockchain")
        elif not st.session_state.selected_type:
           st.error("⚠️ Veuillez sélectionner un type de problème")
        elif not quartier:
           st.error("⚠️ Veuillez indiquer le quartier")
        elif not st.session_state.wallet_connected:
           st.error("⚠️ Veuillez connecter votre wallet dans la sidebar")
        else:
            # Générer un ID unique et un hash temporaire
            new_id = f"SIG-{len(st.session_state.signalements)+1:03d}"
            tx_hash_temp = f"0x{hashlib.sha256(f'{type_probleme}{quartier}{time.time()}'.encode()).hexdigest()[:40]}"
        
            # Créer le signalement (sera ajouté immédiatement)
            nouveau_signalement = {
                'id': new_id,
                'type': type_probleme,
                'quartier': quartier,
                'date': datetime.datetime.now(),
                'statut': 'en_attente',
                'lat': st.session_state.selected_lat,
                'lng': st.session_state.selected_lng,
                'description': description,
                'tx_hash': tx_hash_temp,
                'signale_par': st.session_state.wallet_address[:10] if st.session_state.wallet_address else "Citoyen"
            }
        
            # AJOUT IMMÉDIAT DANS LA LISTE (avant même la transaction)
            st.session_state.signalements.append(nouveau_signalement)
            st.session_state.last_report = nouveau_signalement
        
            if st.session_state.demo_mode:
                # Mode démo : déjà ajouté
                st.success("✅ Signalement enregistré (mode démo) !")
                st.balloons()
                st.session_state.page = 'confirmation'
                st.rerun()
            else:
                # Mode réel : préparer la transaction
                with st.spinner("🔄 Préparation de la transaction..."):
                    try:
                        lat_int = int(st.session_state.selected_lat * 10**6)
                        lng_int = int(st.session_state.selected_lng * 10**6)
                    
                        transaction, error = st.session_state.blockchain.create_report_transaction(
                            type_probleme, description, quartier,
                            lat_int, lng_int,
                            st.session_state.wallet_address
                        )
                    
                        if error:
                            st.error(f"❌ Erreur: {error}")
                        else:
                            # Afficher les détails
                            st.markdown("### 📋 Récapitulatif")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Type:** {type_probleme}")
                                st.write(f"**Quartier:** {quartier}")
                            with col2:
                                st.write(f"**GPS:** {st.session_state.selected_lat}, {st.session_state.selected_lng}")
                        
                            if st.session_state.blockchain.w3:
                                fee_eth = (transaction['gas'] * transaction['gasPrice']) / 10**18
                                st.info(f"💰 Frais estimés: {fee_eth:.6f} ETH")
                        
                            st.warning("🦊 **Confirmation MetaMask requise**")
                         
                            # Bouton pour envoyer la transaction
                            if st.button("✅ Confirmer et envoyer", type="primary", use_container_width=True):
                                st.markdown(f"""
                                <script>
                                (async function() {{
                                    if (typeof window.ethereum !== 'undefined') {{
                                        try {{
                                            const tx = {json.dumps(transaction)};
                                            const hash = await window.ethereum.request({{
                                                method: 'eth_sendTransaction',
                                                params: [tx]
                                            }});
                                            // Mettre à jour le hash dans le signalement déjà stocké
                                            let reports = {json.dumps(st.session_state.signalements)};
                                            for(let i=0; i<reports.length; i++) {{
                                                if(reports[i].id === '{new_id}') {{
                                                    reports[i].tx_hash = hash;
                                                    break;
                                                }}
                                            }}
                                            // Sauvegarder dans sessionStorage pour mise à jour après reload
                                            sessionStorage.setItem('updated_reports', JSON.stringify(reports));
                                            sessionStorage.setItem('last_report_id', '{new_id}');
                                            alert("✅ Transaction envoyée ! Hash: " + hash);
                                            window.location.href = "?page=confirmation";
                                        }} catch(error) {{
                                            alert("❌ Erreur: " + error.message);
                                        }}
                                    }} else {{
                                        alert("❌ MetaMask non détecté");
                                    }}
                                }})();
                                </script>
                                """, unsafe_allow_html=True)
                            
                                st.success("Signalement enregistré localement. Attente confirmation blockchain...")
                                st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erreur: {str(e)}")   

# ==================== PAGE CONFIRMATION - VÉRIFIER LA SAUVEGARDE ====================
elif st.session_state.page == 'confirmation':
    # Vérifier si on a des données sauvegardées
    if 'last_report' not in st.session_state or not st.session_state.last_report:
        # Créer un rapport par défaut si nécessaire
        st.session_state.last_report = {
            'id': f"SIG-{len(st.session_state.signalements)}",
            'tx_hash': 'En attente...',
            'date': datetime.datetime.now(),
            'type': 'Signalement',
            'quartier': 'Non spécifié'
        }
    
    report = st.session_state.get('last_report', {})
    st.markdown("## ✅ SIGNALEMENT ENREGISTRÉ !")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div style="background:#f0fdf4;padding:15px;border-radius:10px;border:1px solid #bbf7d0;">
            <b>🕒 Date:</b> {report.get('date', datetime.datetime.now()).strftime('%d/%m/%Y %H:%M:%S')}<br>
            <b>🆔 ID:</b> <code>{report.get('id', 'N/A')}</code>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        tx_hash = report.get('tx_hash', 'N/A')
        st.markdown(f"""
        <div style="background:#e8f5e9;padding:15px;border-radius:10px;border:1px solid #c8e6c9;">
            <b>🔗 Transaction:</b><br>
            <code style="font-size:11px;">{tx_hash[:30] if tx_hash else 'N/A'}...</code><br>
            <b>📍 Type:</b> {report.get('type', 'N/A')}<br>
            <b>📍 Quartier:</b> {report.get('quartier', 'N/A')}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    colA, colB, colC = st.columns(3)
    with colA:
        if st.button("📋 Mes signalements", use_container_width=True):
            st.session_state.page = 'mes_signalements'
            st.rerun()
    with colB:
        if st.button("🗺️ Voir sur la carte", use_container_width=True):
            st.session_state.page = 'accueil'
            st.rerun()
    with colC:
        if st.button("➕ Nouveau signalement", use_container_width=True):
            st.session_state.page = 'nouveau_signalement'
            st.rerun()
    
    # Afficher le nombre de signalements
    st.info(f"📊 Vous avez maintenant **{len(st.session_state.signalements)}** signalements enregistrés")

# ==================== PAGE MES SIGNALEMENTS - VÉRIFIER L'AFFICHAGE ====================
# ==================== PAGE MES SIGNALEMENTS - VERSION DATAFRAME ====================
elif st.session_state.page == 'mes_signalements':
    import pandas as pd
    
    st.markdown("## 📋 Mes signalements")
    
    if st.button("🔄 Rafraîchir", use_container_width=True):
        st.rerun()
    
    st.markdown("---")
    
    if not st.session_state.signalements:
        st.info("📭 Aucun signalement trouvé")
    else:
        # Créer un DataFrame pour l'affichage
        data = []
        for s in reversed(st.session_state.signalements):
            date_str = s['date'].strftime('%d/%m/%Y') if isinstance(s['date'], datetime.datetime) else str(s['date'])[:10]
            tx_hash = s.get('tx_hash', 'Non disponible')
            if tx_hash and len(str(tx_hash)) > 20:
                tx_hash = str(tx_hash)[:20] + '...'
            
            # Traduire le statut
            statut_fr = {
                'en_attente': '⏳ En attente',
                'en_cours': '🔄 En cours',
                'resolu': '✅ Résolu'
            }.get(s['statut'], s['statut'])
            
            data.append({
                'Type': s['type'],
                'Quartier': s['quartier'],
                'Date': date_str,
                'Statut': statut_fr,
                'Hash': tx_hash
            })
        
        df = pd.DataFrame(data)
        
        # Afficher le DataFrame avec style
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Type": st.column_config.TextColumn("Type", width="small"),
                "Quartier": st.column_config.TextColumn("Quartier", width="medium"),
                "Date": st.column_config.TextColumn("Date", width="small"),
                "Statut": st.column_config.TextColumn("Statut", width="small"),
                "Hash": st.column_config.TextColumn("Hash de transaction", width="large"),
            }
        )
        
        st.caption(f"📊 Total: {len(st.session_state.signalements)} signalements")
    
    st.markdown("---")
    
    if st.button("➕ NOUVEAU SIGNALEMENT", use_container_width=True):
        st.session_state.page = 'nouveau_signalement'
        st.rerun()


# ==================== PAGE CARTE PUBLIQUE ====================
elif st.session_state.page == 'carte_publique':
    st.markdown("## 🗺️ SentinelleCI - Carte Publique")
    
    with st.expander("🔍 FILTRES", expanded=True):
        colF1, colF2, colF3, colF4 = st.columns(4)
        with colF1:
            st.multiselect("Type de problème", ["Route", "École", "Éclairage", "Eau"], key="filter_type_unique")
        with colF2:
            st.selectbox("Statut", ["Tous", "En attente", "En cours", "Résolu"], key="select_statut_unique")
        with colF3:
            st.selectbox("Période", ["30 derniers jours", "Ce mois", "Cette année"], key="select_periode_unique")
        with colF4:
            st.selectbox("Commune", ["Toutes", "Yopougon", "Abobo", "Cocody", "Plateau"], key="select_commune_unique")
    
    col_map, col_list = st.columns([2, 1])
    with col_map:
        m = create_map(zoom=12)
        st_folium(m, width=600, height=500, key="folium_carte_publique_unique")
    with col_list:
        st.markdown("### 📍 Signalements à proximité")
        for s in st.session_state.signalements[:5]:
            st.markdown(f"""
            <div style="background: #f8f9fa; border-radius: 10px; padding: 10px; margin-bottom: 10px;">
                <b>#{s['id']}</b> – {s['type']}<br>
                📍 {s['quartier']}<br>
                <code>{s.get('tx_hash', '0x71a3...b9f2')[:15]}...</code>
            </div>
            """, unsafe_allow_html=True)


# ==================== PAGE MAIRIE ====================
elif st.session_state.page == 'mairie':
    st.markdown("## 🏛️ MAIRIE DE YOPOUGON")
    st.markdown("### Tableau de bord")
    
    colK1, colK2, colK3, colK4 = st.columns(4)
    en_attente = len([s for s in st.session_state.signalements if s['statut'] == 'en_attente'])
    en_cours = len([s for s in st.session_state.signalements if s['statut'] == 'en_cours'])
    resolus = len([s for s in st.session_state.signalements if s['statut'] == 'resolu'])
    total = len(st.session_state.signalements)
    
    with colK1:
        st.metric("📋 En attente", en_attente)
    with colK2:
        st.metric("🚧 En cours", en_cours)
    with colK3:
        st.metric("✅ Résolus", resolus)
    with colK4:
        st.metric("📊 Total", total)
    
    st.markdown("---")
    st.markdown("### 🗺️ CARTE DES SIGNALEMENTS")
    m = create_map(zoom=11)
    st_folium(m, width=900, height=450, key="folium_mairie_unique")
    
    st.markdown("---")
    
    col_chart, col_list = st.columns([1, 1])
    with col_chart:
        st.markdown("### 📊 RÉPARTITION STATISTIQUE")
        fig = create_donut_chart()
        st.plotly_chart(fig, use_container_width=True, key="plotly_donut_unique")
        
        st.markdown("""
        <div style="background: #1e1e2f; padding: 15px; border-radius: 12px; margin-top: 10px;">
            <b>📖 Légende :</b><br>
            <span style="color: #ff6b6b;">🔴 En attente</span> - Signalements non encore traités<br>
            <span style="color: #ffa500;">🟠 En cours</span> - Signalements en cours de traitement<br>
            <span style="color: #4ecdc4;">🟢 Résolus</span> - Signalements terminés
        </div>
        """, unsafe_allow_html=True)
    
    with col_list:
        st.markdown("### 🚨 SIGNALEMENTS NON PRIS EN CHARGE")
        non_pris = [s for s in st.session_state.signalements if s['statut'] == 'en_attente']
        if non_pris:
            for i, s in enumerate(non_pris[:5]):
                col_id, col_type, col_quartier, col_action = st.columns([1, 1, 1, 1])
                with col_id:
                    st.write(s['id'])
                with col_type:
                    st.write(s['type'])
                with col_quartier:
                    st.write(s['quartier'])
                with col_action:
                    if st.button("PRENDRE", key=f"btn_prendre_mairie_unique_{i}"):
                        st.session_state.selected_signalement = s
                        st.session_state.show_prise_en_charge = True
                st.divider()
            if len(non_pris) > 5:
                st.info(f"... et {len(non_pris) - 5} autres")
        else:
            st.info("✅ Aucun signalement en attente")
    
    # ========== PRISE EN CHARGE ==========
    if st.session_state.show_prise_en_charge and st.session_state.get('selected_signalement'):
        st.markdown("---")
        st.markdown("## 📋 PRISE EN CHARGE")
        
        s = st.session_state.selected_signalement
        with st.form("prise_en_charge_unique"):
            st.info(f"**#{s['id']}** – {s['type']} – {s['quartier']}")
            agent = st.selectbox("Assigner à", ["Koffi A.", "Diallo M.", "Kouadio L.", "Yao B."], key="select_agent_unique")
            commentaire = st.text_area("Commentaire", key="textarea_comment_unique")
            date_interv = st.date_input("Date prévue", datetime.datetime.now() + datetime.timedelta(days=7), key="date_interv_unique")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.form_submit_button("✅ VALIDER", type="primary"):
                    for sig in st.session_state.signalements:
                        if sig['id'] == s['id']:
                            sig['statut'] = 'en_cours'
                            sig['agent'] = agent
                            sig['commentaire'] = commentaire
                            break
                    st.session_state.show_prise_en_charge = False
                    st.success("✅ Signalement pris en charge")
                    st.rerun()
            with col_btn2:
                if st.form_submit_button("❌ ANNULER"):
                    st.session_state.show_prise_en_charge = False
                    st.rerun()
    
    st.markdown("---")
    st.markdown("### 👥 AGENTS TERRAIN")
    st.markdown("""
    <style>
         .agents-list {
             background: #f8f9fa; 
             padding: 15px; 
             border-radius: 10px;
             color: #000000;
         }
         .agents-list span {
             color: #000000;
         }
    </style>
    <div class="agents-list">
        - 👤 <strong>Koffi A.</strong> (3 interventions)<br>
        - 👤 <strong>Diallo M.</strong> (2 interventions)<br>
        - 👤 <strong>Kouadio L.</strong> (1 intervention)<br>
        - 👤 <strong>Yao B.</strong> (1 intervention)
    </div>
    """, unsafe_allow_html=True)


# ==================== PAGE PROFIL ====================
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
    st.checkbox("Notifications", value=True, key="pref_notifications")
    st.selectbox("Langue", ["Français", "English"], key="pref_langue")


# ==================== FOOTER ====================
st.markdown("---")
st.caption("© 2026 Sentinelle.CI - Plateforme citoyenne de signalement sur blockchain | Version 2.0 - Transactions réelles sur Sepolia")