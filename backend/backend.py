from flask import Flask, request, jsonify
from flask_cors import CORS
from web3 import Web3
import os
import json
from datetime import datetime
import hashlib

app = Flask(__name__)
CORS(app)  # Important pour Streamlit Cloud

# Configuration Blockchain
RPC_URLS = [
    "https://rpc.ankr.com/eth_sepolia",
    "https://ethereum-sepolia.publicnode.com",
    "https://sepolia.gateway.tenderly.co",
    "https://1rpc.io/sepolia",
]

CONTRACT_ADDRESS = "0xd9145CCE52D386f254917e481eB44e9943F39138"

# ABI simplifiée
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
    }
]

# Initialiser Web3
w3 = None
contract = None

def connect_web3():
    global w3, contract
    for rpc_url in RPC_URLS:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 10}))
            if w3.is_connected():
                contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
                print(f"✅ Connecté à {rpc_url}")
                return True
        except Exception as e:
            print(f"❌ Erreur connexion {rpc_url}: {e}")
    return False

# Connexion au démarrage
connect_web3()

# Variables d'environnement pour le sponsor
SPONSOR_PRIVATE_KEY = os.environ.get('SPONSOR_PRIVATE_KEY')
SPONSOR_ADDRESS = os.environ.get('SPONSOR_ADDRESS', '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0')

@app.route('/api/sponsor', methods=['POST'])
def sponsor_report():
    """Endpoint pour envoyer une transaction blockchain"""
    try:
        if not w3 or not contract:
            return jsonify({'error': 'Blockchain non connectée'}), 503
        
        data = request.json
        print(f"📝 Reçu: {data}")
        
        # Vérifier si on utilise le mode sponsor ou simulation
        use_real_tx = os.environ.get('USE_REAL_TX', 'false').lower() == 'true'
        
        if use_real_tx and SPONSOR_PRIVATE_KEY:
            # Transaction réelle sur Sepolia
            lat_int = int(float(data['lat']) * 10**6)
            lng_int = int(float(data['lng']) * 10**6)
            
            # Construire la transaction
            transaction = contract.functions.createReport(
                data['type'],
                data['description'],
                data['quartier'],
                lat_int,
                lng_int
            ).build_transaction({
                'from': SPONSOR_ADDRESS,
                'nonce': w3.eth.get_transaction_count(SPONSOR_ADDRESS),
                'gas': 500000,
                'gasPrice': w3.eth.gas_price
            })
            
            # Signer
            signed_txn = w3.eth.account.sign_transaction(transaction, SPONSOR_PRIVATE_KEY)
            
            # Envoyer
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            
            print(f"✅ Transaction envoyée: {tx_hash_hex}")
            return jsonify({'tx_hash': tx_hash_hex}), 200
        else:
            # Mode simulation/démo
            dummy_hash = f"0x{hashlib.sha256(f'{data}{datetime.now().isoformat()}'.encode()).hexdigest()[:64]}"
            print(f"🔷 Mode démo: {dummy_hash}")
            return jsonify({'tx_hash': dummy_hash}), 200
            
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint pour vérifier que le backend fonctionne"""
    return jsonify({
        'status': 'ok',
        'blockchain_connected': w3 is not None and w3.is_connected(),
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/api/contract-info', methods=['GET'])
def contract_info():
    """Informations sur le contrat blockchain"""
    return jsonify({
        'contract_address': CONTRACT_ADDRESS,
        'network': 'Sepolia',
        'connected': w3 is not None and w3.is_connected()
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
