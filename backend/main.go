package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"math/big"
	"net/http"
	"os"

	"github.com/ethereum/go-ethereum/common"
	"github.com/ethereum/go-ethereum/common/hexutil"
	"github.com/ethereum/go-ethereum/core/types"
	"github.com/ethereum/go-ethereum/crypto"
	"github.com/ethereum/go-ethereum/ethclient"
)

type ReportRequest struct {
	UserAddress string `json:"userAddress"`
	Severity    uint8  `json:"severity"`
	Content     string `json:"content"`
}

type ReportResponse struct {
	TxHash string `json:"txHash"`
}

var (
	privateKeyHex = os.Getenv("PRIVATE_KEY") // TA clé privée (sans 0x)
	rpcURL        = os.Getenv("RPC_URL")     // ex: https://sepolia.infura.io/v3/...
	contractAddr  = common.HexToAddress(os.Getenv("CONTRACT_ADDRESS"))
)

func main() {
	if privateKeyHex == "" || rpcURL == "" || contractAddr == (common.Address{}) {
		log.Fatal("Missing env: PRIVATE_KEY, RPC_URL, CONTRACT_ADDRESS")
	}

	http.HandleFunc("/report", handleReport)
	log.Println("Go relayer running on :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}

func handleReport(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "POST only", http.StatusMethodNotAllowed)
		return
	}

	var req ReportRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	txHash, err := submitReport(req.UserAddress, req.Severity, req.Content)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(ReportResponse{TxHash: txHash})
}

func submitReport(userAddrHex string, severity uint8, content string) (string, error) {
	// 1. Connexion au réseau
	client, err := ethclient.Dial(rpcURL)
	if err != nil {
		return "", err
	}
	defer client.Close()

	// 2. Charger la clé privée
	privateKey, err := crypto.HexToECDSA(privateKeyHex)
	if err != nil {
		return "", err
	}
	publicKey := privateKey.Public()
	publicKeyECDSA, ok := publicKey.(*ecdsa.PublicKey)
	if !ok {
		return "", fmt.Errorf("invalid public key")
	}
	fromAddress := crypto.PubkeyToAddress(*publicKeyECDSA)

	// 3. Construire le call data
	// ABI du contrat – tu peux la générer avec abigen ou la coder en dur
	// Pour l'exemple, utilisons une fonction "report(uint8,string,address)"
	// Encodage manuel (à adapter selon ton ABI réel)
	// Mieux : utiliser le package "github.com/ethereum/go-ethereum/accounts/abi"
	// Ici on simplifie : tu remplaceras par l'encodage correct
	methodSignature := "report(uint8,string,address)"
	methodID := crypto.Keccak256([]byte(methodSignature))[:4]

	// Encodage des arguments (padding 32 bytes)
	severityEnc := common.LeftPadBytes([]byte{byte(severity)}, 32)
	contentEnc := common.LeftPadBytes([]byte(content), 32) // attention : string doit être encodé différemment (offset + length)
	userAddrEnc := common.LeftPadBytes(common.HexToAddress(userAddrHex).Bytes(), 32)

	data := append(methodID, severityEnc...)
	data = append(data, contentEnc...)
	data = append(data, userAddrEnc...)

	// 4. Préparer la transaction
	nonce, err := client.PendingNonceAt(context.Background(), fromAddress)
	if err != nil {
		return "", err
	}
	gasPrice, err := client.SuggestGasPrice(context.Background())
	if err != nil {
		return "", err
	}
	gasLimit := uint64(300000) // à ajuster

	tx := types.NewTransaction(nonce, contractAddr, big.NewInt(0), gasLimit, gasPrice, data)

	// 5. Signer
	chainID, err := client.NetworkID(context.Background())
	if err != nil {
		return "", err
	}
	signer := types.LatestSignerForChainID(chainID)
	signedTx, err := types.SignTx(tx, signer, privateKey)
	if err != nil {
		return "", err
	}

	// 6. Envoyer
	err = client.SendTransaction(context.Background(), signedTx)
	if err != nil {
		return "", err
	}

	return signedTx.Hash().Hex(), nil
}