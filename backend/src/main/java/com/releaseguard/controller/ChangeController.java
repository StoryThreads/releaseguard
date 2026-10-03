package com.releaseguard.controller;

import com.releaseguard.dto.change.ChangeResponse;
import com.releaseguard.dto.change.CreateChangeRequest;
import com.releaseguard.entity.Change;
import com.releaseguard.service.ChangeService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/changes")
public class ChangeController {

    private final ChangeService changeService;
    private final com.releaseguard.service.DashboardService dashboardService;

    public ChangeController(
        ChangeService changeService,
        com.releaseguard.service.DashboardService dashboardService
    ) {
        this.changeService = changeService;
        this.dashboardService = dashboardService;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ChangeResponse createChange(
        @Valid @RequestBody CreateChangeRequest request
    ) {

        Change change = changeService.createChange(
            request.getSourceId(),
            request.getExternalChangeId(),
            request.getTitle(),
            request.getAuthor(),
            request.getBaseRevision(),
            request.getHeadRevision(),
            request.getStatus()
        );

        return toResponse(change);
    }

    @GetMapping("/recent")
    public List<com.releaseguard.dto.analysis.ChangeAnalysisDetailsResponse> getRecentChanges(
        @RequestParam(defaultValue = "50") int limit
    ) {
        return dashboardService.getRecentChanges(limit);
    }

    @GetMapping("/{id}")
    public ChangeResponse getChange(@PathVariable Long id) {

        return toResponse(changeService.getChange(id));
    }

    @GetMapping("/{id}/analysis")
    public com.releaseguard.dto.analysis.ChangeAnalysisDetailsResponse getChangeAnalysis(
        @PathVariable Long id
    ) {
        return dashboardService.getChangeAnalysisDetails(id);
    }

    @GetMapping("/{id}/status")
    public com.releaseguard.dto.analysis.AnalysisStatusResponse getChangeStatus(
        @PathVariable Long id
    ) {
        return dashboardService.getAnalysisStatus(id);
    }

    @GetMapping("/source/{sourceId}")
    public List<ChangeResponse> getChangesBySource(
        @PathVariable Long sourceId
    ) {

        return changeService.getChangesBySource(sourceId)
            .stream()
            .map(this::toResponse)
            .toList();
    }

    private ChangeResponse toResponse(Change change) {

        return new ChangeResponse(
            change.getId(),
            change.getSource().getId(),
            change.getExternalChangeId(),
            change.getTitle(),
            change.getAuthor(),
            change.getBaseRevision(),
            change.getHeadRevision(),
            change.getStatus(),
            change.getCreatedAt(),
            change.getUpdatedAt()
        );
    }
}
