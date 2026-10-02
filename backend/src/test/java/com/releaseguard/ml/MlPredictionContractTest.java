package com.releaseguard.ml;

import com.releaseguard.analyzer.AnalyzerType;
import com.releaseguard.analyzer.Finding;
import com.releaseguard.analyzer.FindingSeverity;
import com.releaseguard.analyzer.FindingType;
import com.releaseguard.domain.ChangeSnapshot;
import com.releaseguard.ml.dto.MlPredictionResponse;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

class MlPredictionContractTest {

    @Test
    void predictionResponseCarriesVersionedRiskContract() {

        MlPredictionResponse response =
            new MlPredictionResponse();

        response.setRiskLevel("HIGH");
        response.setRiskScore(75.0);
        response.setModelName("xgboost_candidate");
        response.setModelVersion("1.0.0");
        response.setFeatureVersion("1.0.0");
        response.setDatasetVersion("1.0.0");

        assertEquals("HIGH", response.getRiskLevel());
        assertEquals(75.0, response.getRiskScore());
        assertEquals(
            "xgboost_candidate",
            response.getModelName()
        );
        assertEquals("1.0.0", response.getModelVersion());
        assertEquals("1.0.0", response.getFeatureVersion());
        assertEquals("1.0.0", response.getDatasetVersion());
    }

    @Test
    void rawSnapshotAndFindingsFormTheMlRequestContract() {

        ChangeSnapshot snapshot = new ChangeSnapshot();
        snapshot.setPullRequestNumber(42L);
        snapshot.setOwner("owner");
        snapshot.setRepository("repo");

        Finding finding = new Finding(
            AnalyzerType.CODE,
            FindingType.CODE_ISSUE,
            FindingSeverity.HIGH,
            "CODE-001",
            "Test finding",
            "Test message",
            "src/Test.java",
            10
        );

        var request =
            new com.releaseguard.ml.dto.MlPredictionRequest(
                snapshot,
                List.of(finding)
            );

        assertNotNull(request.getChangeSnapshot());
        assertEquals(42L, request.getChangeSnapshot().getPullRequestNumber());
        assertEquals(1, request.getFindings().size());
        assertEquals(
            FindingSeverity.HIGH,
            request.getFindings().get(0).severity()
        );
    }
}
