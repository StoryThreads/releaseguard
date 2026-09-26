package com.releaseguard.controller;

import com.releaseguard.dto.source.CreateSourceRequest;
import com.releaseguard.dto.source.SourceResponse;
import com.releaseguard.entity.Source;
import com.releaseguard.service.SourceService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/sources")
public class SourceController {

    private final SourceService sourceService;

    public SourceController(SourceService sourceService) {
        this.sourceService = sourceService;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public SourceResponse createSource(
        @Valid @RequestBody CreateSourceRequest request
    ) {

        Source source = sourceService.createSource(
            request.getProjectId(),
            request.getProvider(),
            request.getRepositoryOwner(),
            request.getRepositoryName(),
            request.getDefaultBranch()
        );

        return toResponse(source);
    }

    @GetMapping("/{id}")
    public SourceResponse getSource(@PathVariable Long id) {

        return toResponse(sourceService.getSource(id));
    }

    @GetMapping("/project/{projectId}")
    public List<SourceResponse> getSourcesByProject(
        @PathVariable Long projectId
    ) {

        return sourceService.getSourcesByProject(projectId)
            .stream()
            .map(this::toResponse)
            .toList();
    }

    private SourceResponse toResponse(Source source) {

        return new SourceResponse(
            source.getId(),
            source.getProject().getId(),
            source.getProvider(),
            source.getRepositoryOwner(),
            source.getRepositoryName(),
            source.getDefaultBranch(),
            source.getCreatedAt(),
            source.getUpdatedAt()
        );
    }
}
