package com.releaseguard.service;

import com.releaseguard.entity.Project;
import com.releaseguard.exception.ConflictException;
import com.releaseguard.exception.ResourceNotFoundException;
import com.releaseguard.repository.ProjectRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.List;

@Service
@Transactional
public class ProjectService {

    private final ProjectRepository projectRepository;

    public ProjectService(ProjectRepository projectRepository) {
        this.projectRepository = projectRepository;
    }

    public Project createProject(String name, String description) {

        if (projectRepository.existsByName(name)) {
            throw new ConflictException(
                "Project already exists with name: " + name
            );
        }

        Project project = new Project();

        project.setName(name);
        project.setDescription(description);

        return projectRepository.save(project);
    }

    @Transactional(readOnly = true)
    public List<Project> getAllProjects() {
        return projectRepository.findAll();
    }

    @Transactional(readOnly = true)
    public Project getProject(Long id) {
        return projectRepository.findById(id)
            .orElseThrow(() ->
                new ResourceNotFoundException(
                    "Project not found: " + id
                )
            );
    }

    public Project getOrCreateProject(String name, String description) {
        return projectRepository.findByName(name)
            .orElseGet(() -> {
                Project p = new Project();
                p.setName(name);
                p.setDescription(description != null ? description : "GitHub repository " + name);
                return projectRepository.save(p);
            });
    }
}
