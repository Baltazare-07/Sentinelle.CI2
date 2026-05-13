// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract SentinelleReports {
    struct Report {
        address citizen;
        string reportType;
        string description;
        string quartier;
        int256 latitude;
        int256 longitude;
        uint256 timestamp;
        uint256 upvotes;
        uint256 downvotes;
        bool isResolved;
    }

    Report[] public reports;
    mapping(uint256 => mapping(address => bool)) public hasVoted; // reportId => voter => voted
    mapping(address => uint256) public reputationScore;

    event ReportCreated(
        uint256 indexed reportId,
        address indexed citizen,
        string reportType,
        uint256 timestamp
    );
    event Voted(uint256 indexed reportId, address indexed voter, bool isUpvote);
    event ReportResolved(uint256 indexed reportId);

    function createReport(
        address _citizen,                          // <-- NOUVEAU
        string memory _reportType,
        string memory _description,
        string memory _quartier,
        int256 _latitude,
        int256 _longitude
    ) external {
        reports.push(Report({
            citizen: _citizen,                     // <-- utiliser _citizen
            reportType: _reportType,
            description: _description,
            quartier: _quartier,
            latitude: _latitude,
            longitude: _longitude,
            timestamp: block.timestamp,
            upvotes: 0,
            downvotes: 0,
            isResolved: false
        }));
        uint256 reportId = reports.length - 1;
        reputationScore[_citizen] += 10;           // <-- plus de 10 points pour le citoyen
        emit ReportCreated(reportId, _citizen, _reportType, block.timestamp);
    }
        uint256 reportId = reports.length - 1;
        // Ajouter 10 points de réputation pour avoir signalé
        reputationScore[msg.sender] += 10;
        emit ReportCreated(reportId, msg.sender, _reportType, block.timestamp);
    }

    function vote(uint256 _reportId, bool _isUpvote) external {
        require(_reportId < reports.length, "Report does not exist");
        require(!hasVoted[_reportId][msg.sender], "Already voted");

        if (_isUpvote) {
            reports[_reportId].upvotes++;
            // +1 point de réputation pour upvote utile
            reputationScore[msg.sender] += 1;
        } else {
            reports[_reportId].downvotes++;
        }
        hasVoted[_reportId][msg.sender] = true;
        emit Voted(_reportId, msg.sender, _isUpvote);
    }

    function resolveReport(uint256 _reportId) external {
        require(_reportId < reports.length, "Report does not exist");
        // Seul le créateur ou un admin (toi) peut résoudre
        require(msg.sender == reports[_reportId].citizen || msg.sender == owner(), "Not authorized");
        reports[_reportId].isResolved = true;
        // Bonus de 20 points pour résolution
        reputationScore[reports[_reportId].citizen] += 20;
        emit ReportResolved(_reportId);
    }

    function owner() public view returns (address) {
        return 0x4163C3be2cfB0C1856AE0bdEcb6535A41dE3047B; // Remplace par ton adresse MetaMask
    }

    function getReportCount() public view returns (uint256) {
        return reports.length;
    }

    function getReport(uint256 _reportId) public view returns (
        address citizen,
        string memory reportType,
        string memory description,
        string memory quartier,
        int256 latitude,
        int256 longitude,
        uint256 timestamp,
        uint256 upvotes,
        uint256 downvotes,
        bool isResolved
    ) {
        Report storage r = reports[_reportId];
        return (
            r.citizen,
            r.reportType,
            r.description,
            r.quartier,
            r.latitude,
            r.longitude,
            r.timestamp,
            r.upvotes,
            r.downvotes,
            r.isResolved
        );
    }
}