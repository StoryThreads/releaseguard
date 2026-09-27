package com.releaseguard.analysis;

import com.releaseguard.analysis.dto.AnalyzePullRequestRequest;
import com.releaseguard.analysis.dto.AnalyzePullRequestResponse;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/analysis")
public class AnalysisController {

    private final AnalysisService analysisService;

    public AnalysisController(
        AnalysisService analysisService
    ) {
        this.analysisService = analysisService;
    }

    @PostMapping("/pr")
    public ResponseEntity<AnalyzePullRequestResponse> analyzePullRequest(
        @Valid @RequestBody AnalyzePullRequestRequest request
    ) {

        AnalyzePullRequestResponse response =
            analysisService.analyzePullRequest(
                request.getOwner(),
                request.getRepository(),
                request.getPullRequestNumber()
            );

        return ResponseEntity.ok(response);
    }
}
