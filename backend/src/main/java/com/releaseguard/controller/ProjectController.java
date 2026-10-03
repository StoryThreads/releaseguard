package com.releaseguard.controller;

import com.releaseguard.dto.project.CreateProjectRequest;
import com.releaseguard.dto.project.ProjectResponse;
import com.releaseguard.entity.Project;
import com.releaseguard.service.ProjectService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/projects")
public class ProjectController {

    private final ProjectService projectService;
    private final com.releaseguard.service.DashboardService dashboardService;

    public ProjectController(
        ProjectService projectService,
        com.releaseguard.service.DashboardService dashboardService
    ) {
        this.projectService = projectService;
        this.dashboardService = dashboardService;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ProjectResponse createProject(
        @Valid @RequestBody CreateProjectRequest request
    ) {

        Project project = projectService.createProject(
            request.getName(),
            request.getDescription()
        );

        return toResponse(project);
    }

    @GetMapping
    public List<ProjectResponse> getAllProjects() {

        return projectService.getAllProjects()
            .stream()
            .map(this::toResponse)
            .toList();
    }

    @GetMapping("/{id}")
    public ProjectResponse getProject(@PathVariable Long id) {

        return toResponse(projectService.getProject(id));
    }

    @GetMapping("/{id}/summary")
    public com.releaseguard.dto.project.ProjectSummaryResponse getProjectSummary(
        @PathVariable Long id
    ) {
        return dashboardService.getProjectSummary(id);
    }

    @GetMapping("/{id}/changes")
    public List<com.releaseguard.dto.analysis.ChangeAnalysisDetailsResponse> getProjectChanges(
        @PathVariable Long id
    ) {
        return dashboardService.getChangesByProject(id);
    }

    private ProjectResponse toResponse(Project project) {

        return new ProjectResponse(
            project.getId(),
            project.getName(),
            project.getDescription(),
            project.getCreatedAt(),
            project.getUpdatedAt()
        );
    }
}
