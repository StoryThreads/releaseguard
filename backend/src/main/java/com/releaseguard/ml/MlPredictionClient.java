package com.releaseguard.ml;

import com.releaseguard.analyzer.Finding;
import com.releaseguard.domain.ChangeSnapshot;
import com.releaseguard.ml.dto.MlPredictionRequest;
import com.releaseguard.ml.dto.MlPredictionResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

import java.util.List;

@Component
public class MlPredictionClient {

    private final RestClient restClient;

    public MlPredictionClient(
        @Value("${releaseguard.ml-service.url:http://localhost:8000}")
        String baseUrl
    ) {
        this.restClient = RestClient.builder()
            .baseUrl(baseUrl)
            .build();
    }

    public MlPredictionResponse predict(
        ChangeSnapshot snapshot,
        List<Finding> findings
    ) {

        try {
            return restClient.post()
                .uri("/api/v1/predict")
                .body(
                    new MlPredictionRequest(
                        snapshot,
                        findings
                    )
                )
                .retrieve()
                .body(MlPredictionResponse.class);

        } catch (RestClientException exception) {
            throw new MlPredictionException(
                "ML prediction service is unavailable",
                exception
            );
        }
    }
}
