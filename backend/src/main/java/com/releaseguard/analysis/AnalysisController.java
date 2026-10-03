package com.releaseguard.analysis;

import com.releaseguard.analysis.dto.AnalyzePullRequestRequest;
import com.releaseguard.analysis.dto.AnalyzePullRequestResponse;
import com.releaseguard.analyzer.AnalyzerContext;
import com.releaseguard.analyzer.AnalyzerEngine;
import com.releaseguard.analyzer.Finding;
import com.releaseguard.domain.ChangeSnapshot;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/analysis")
public class AnalysisController {

    private final AnalysisService analysisService;
    private final AnalyzerEngine analyzerEngine;

    public AnalysisController(
        AnalysisService analysisService,
        AnalyzerEngine analyzerEngine
    ) {
        this.analysisService = analysisService;
        this.analyzerEngine = analyzerEngine;
    }

    @PostMapping("/pr")
    public ResponseEntity<AnalyzePullRequestResponse> analyzePullRequest(
        @Valid @RequestBody AnalyzePullRequestRequest request
    ) {

        AnalyzePullRequestResponse response =
            analysisService.analyzePullRequest(
                request.getProjectId(),
                request.getOwner(),
                request.getRepository(),
                request.getPullRequestNumber()
            );

        return ResponseEntity.ok(response);
    }

    @PostMapping("/snapshot")
    public ResponseEntity<Map<String, Object>> analyzeSnapshot(
        @RequestBody ChangeSnapshot snapshot
    ) {
        AnalyzerContext context = new AnalyzerContext(snapshot);
        List<Finding> findings = analyzerEngine.analyze(context);

        return ResponseEntity.ok(Map.of(
            "snapshot", snapshot,
            "findings", findings
        ));
    }
}
