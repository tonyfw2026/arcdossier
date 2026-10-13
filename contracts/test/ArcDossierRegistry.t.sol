// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ArcDossierRegistry} from "../src/ArcDossierRegistry.sol";

contract OtherPublisher {
    function anchor(ArcDossierRegistry registry) external {
        registry.anchorReport(bytes32(uint256(1)), bytes32(uint256(2)), 1, 1);
    }
}

contract ArcDossierRegistryTest {
    function testPublisherIsDeployer() public {
        ArcDossierRegistry registry = new ArcDossierRegistry();
        require(registry.publisher() == address(this), "wrong publisher");
    }

    function testPublisherCanAnchorAndReadReport() public {
        ArcDossierRegistry registry = new ArcDossierRegistry();
        bytes32 projectId = keccak256("arc.network");
        bytes32 reportHash = keccak256("report-json");

        registry.anchorReport(projectId, reportHash, 1_791_840_000, 1);

        (bytes32 storedHash, uint64 generatedAt, uint32 scoringVersion) =
            registry.latestReport(projectId);
        require(storedHash == reportHash, "wrong hash");
        require(generatedAt == 1_791_840_000, "wrong timestamp");
        require(scoringVersion == 1, "wrong scoring version");
    }

    function testOtherAddressCannotAnchor() public {
        ArcDossierRegistry registry = new ArcDossierRegistry();
        OtherPublisher other = new OtherPublisher();

        try other.anchor(registry) {
            revert("unauthorized anchor succeeded");
        } catch {}
    }

    function testEmptyValuesAreRejected() public {
        ArcDossierRegistry registry = new ArcDossierRegistry();

        try registry.anchorReport(bytes32(0), bytes32(uint256(1)), 1, 1) {
            revert("empty project accepted");
        } catch {}

        try registry.anchorReport(bytes32(uint256(1)), bytes32(0), 1, 1) {
            revert("empty report hash accepted");
        } catch {}
    }
}

