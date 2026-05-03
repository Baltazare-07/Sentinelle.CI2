const express = require('express');
const cors = require('cors');
const crypto = require('crypto');

const app = express();
app.use(cors());
app.use(express.json({ limit: '50mb' }));

// Stockage en mémoire
let signalements = [];

// Fonction pour calculer le hash des données
function calculateDataHash(data) {
    return crypto
        .createHash('sha256')
        .update(JSON.stringify(data))
        .digest('hex');
}

// Fonction pour enregistrer sur blockchain (simulation)
async function enregistrerSurBlockchain(signalement) {
    try {
        const dataHash = calculateDataHash(signalement);
        const simulatedTxHash = '0x' + crypto.randomBytes(16).toString('hex');
        const simulatedBlockNumber = Math.floor(Math.random() * 10000000);

        return {
            success: true,
            tx_hash: simulatedTxHash,
            block_number: simulatedBlockNumber,
            data_hash: dataHash,
            blockchain_url: `https://sepolia.etherscan.io/tx/${simulatedTxHash}`
        };
    } catch (error) {
        console.error('Erreur blockchain:', error);
        return { success: false, error: error.message };
    }
}

// Routes
app.get('/api/signalements', (req, res) => {
    res.json(signalements);
});

app.post('/api/signalements', async (req, res) => {
    try {
        const { type, description, quartier, latitude, longitude } = req.body;

        const newSignalement = {
            type: type,
            description: description || '',
            quartier: quartier || 'Non spécifié',
            latitude: latitude,
            longitude: longitude,
            utilisateur: 'Citoyen',
            date: new Date().toISOString(),
            statut: 'en_attente',
            created_at: new Date().toISOString()
        };

        console.log(`📝 Enregistrement du signalement...`);

        const blockchainResult = await enregistrerSurBlockchain(newSignalement);

        if (blockchainResult.success) {
            const blockchainId = blockchainResult.tx_hash;

            newSignalement.id = blockchainId;
            newSignalement.tx_hash = blockchainResult.tx_hash;
            newSignalement.block_number = blockchainResult.block_number;
            newSignalement.data_hash = blockchainResult.data_hash;
            newSignalement.blockchain_url = blockchainResult.blockchain_url;
            newSignalement.blockchain_status = 'confirmed';

            signalements.push(newSignalement);

            console.log(`✅ Signalement enregistré: ${blockchainId}`);

            res.status(201).json({
                id: blockchainId,
                tx_hash: blockchainResult.tx_hash,
                block_number: blockchainResult.block_number,
                blockchain_url: blockchainResult.blockchain_url,
                data_hash: blockchainResult.data_hash,
                message: `Signalement enregistré sur blockchain`
            });
        } else {
            res.status(500).json({ error: 'Échec blockchain', details: blockchainResult.error });
        }
    } catch (error) {
        console.error('Erreur:', error);
        res.status(500).json({ error: error.message });
    }
});

// Pour Render - utiliser le port fourni par l'environnement
const PORT = process.env.PORT || 3001;
app.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 Backend API sur le port ${PORT}`);
});