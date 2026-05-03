// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract Signalement {
    struct SignalementStruct {
        uint256 id;
        address auteur;
        string typeProbleme;   // "Route", "Eau", "École", "Éclairage"
        string quartier;
        string description;
        int256 lat;            // latitude * 10^6
        int256 lng;            // longitude * 10^6
        string statut;         // "en_attente", "en_cours", "resolu"
        uint256 dateCreation;
    }

    mapping(uint256 => SignalementStruct) private signalements;
    uint256 private compteurId;

    // Événements
    event SignalementCree(uint256 indexed id, address auteur, string typeProbleme);
    event StatutMisAJour(uint256 indexed id, string nouveauStatut);

    // Créer un signalement
    function creerSignalement(
        string memory _typeProbleme,
        string memory _quartier,
        string memory _description,
        int256 _lat,
        int256 _lng
    ) external returns (uint256) {
        compteurId++;
        uint256 newId = compteurId;

        signalements[newId] = SignalementStruct({
            id: newId,
            auteur: msg.sender,
            typeProbleme: _typeProbleme,
            quartier: _quartier,
            description: _description,
            lat: _lat,
            lng: _lng,
            statut: "en_attente",
            dateCreation: block.timestamp
        });

        emit SignalementCree(newId, msg.sender, _typeProbleme);
        return newId;
    }

    // Mettre à jour le statut
    function mettreAJourStatut(uint256 _id, string memory _nouveauStatut) external {
        require(_id > 0 && _id <= compteurId, "ID invalide");
        require(msg.sender == 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266, "Non autorise");
        signalements[_id].statut = _nouveauStatut;
        emit StatutMisAJour(_id, _nouveauStatut);
    }

    // Récupérer tous les signalements
    function getAllSignalements() external view returns (SignalementStruct[] memory) {
        SignalementStruct[] memory result = new SignalementStruct[](compteurId);
        for (uint256 i = 1; i <= compteurId; i++) {
            result[i - 1] = signalements[i];
        }
        return result;
    }

    // Récupérer un signalement par ID
    function getSignalement(uint256 _id) external view returns (SignalementStruct memory) {
        require(_id > 0 && _id <= compteurId, "ID invalide");
        return signalements[_id];
    }

    // Compter les signalements
    function getNombreSignalements() external view returns (uint256) {
        return compteurId;
    }
}