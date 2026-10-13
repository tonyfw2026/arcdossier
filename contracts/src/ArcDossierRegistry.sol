// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title ArcDossierRegistry
/// @notice Anchors compact ArcDossier report receipts. Full reports remain offchain.
contract ArcDossierRegistry {
    struct ReportReceipt {
        bytes32 reportHash;
        uint64 generatedAt;
        uint32 scoringVersion;
    }

    address public immutable publisher;
    mapping(bytes32 projectId => ReportReceipt receipt) public latestReport;

    error NotPublisher();
    error EmptyProjectId();
    error EmptyReportHash();

    event ReportAnchored(
        bytes32 indexed projectId,
        bytes32 indexed reportHash,
        uint64 generatedAt,
        uint32 scoringVersion,
        address indexed publisher
    );

    constructor() {
        publisher = msg.sender;
    }

    function anchorReport(
        bytes32 projectId,
        bytes32 reportHash,
        uint64 generatedAt,
        uint32 scoringVersion
    ) external {
        if (msg.sender != publisher) revert NotPublisher();
        if (projectId == bytes32(0)) revert EmptyProjectId();
        if (reportHash == bytes32(0)) revert EmptyReportHash();

        latestReport[projectId] = ReportReceipt({
            reportHash: reportHash,
            generatedAt: generatedAt,
            scoringVersion: scoringVersion
        });

        emit ReportAnchored(projectId, reportHash, generatedAt, scoringVersion, msg.sender);
    }
}

