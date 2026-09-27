package com.releaseguard.service;

import com.releaseguard.entity.Project;
import com.releaseguard.entity.Source;
import com.releaseguard.exception.ConflictException;
import com.releaseguard.exception.ResourceNotFoundException;
import com.releaseguard.repository.SourceRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@Transactional
public class SourceService {

    private final SourceRepository sourceRepository;
    private final ProjectService projectService;

    public SourceService(
        SourceRepository sourceRepository,
        ProjectService projectService
    ) {
        this.sourceRepository = sourceRepository;
        this.projectService = projectService;
    }

    public Source createSource(
        Long projectId,
        String provider,
        String repositoryOwner,
        String repositoryName,
        String defaultBranch
    ) {

        Project project = projectService.getProject(projectId);

        if (sourceRepository
            .existsByProjectIdAndProviderAndRepositoryOwnerAndRepositoryName(
                projectId,
                provider,
                repositoryOwner,
                repositoryName
            )) {

            throw new ConflictException(
                "Repository is already registered with this project"
            );
        }

        Source source = new Source();

        source.setProject(project);
        source.setProvider(provider);
        source.setRepositoryOwner(repositoryOwner);
        source.setRepositoryName(repositoryName);
        source.setDefaultBranch(defaultBranch);

        return sourceRepository.save(source);
    }

    @Transactional(readOnly = true)
    public List<Source> getSourcesByProject(Long projectId) {

        // Verify that the project exists.
        projectService.getProject(projectId);

        return sourceRepository.findByProjectId(projectId);
    }

    @Transactional(readOnly = true)
    public Source getGitHubSource(String repositoryOwner, String repositoryName) {

        List<Source> sources =
            sourceRepository.findByProviderIgnoreCaseAndRepositoryOwnerIgnoreCaseAndRepositoryNameIgnoreCase(
                "github",
                repositoryOwner,
                repositoryName
            );

        if (sources.isEmpty()) {
            throw new ResourceNotFoundException(
                "GitHub source not found for repository: "
                    + repositoryOwner + "/" + repositoryName
            );
        }

        if (sources.size() > 1) {
            throw new ConflictException(
                "Multiple GitHub sources found for repository: "
                    + repositoryOwner + "/" + repositoryName
                    + ". Repository analysis is ambiguous."
            );
        }

        return sources.get(0);
    }

    @Transactional(readOnly = true)
    public Source getSource(Long id) {

        return sourceRepository.findById(id)
            .orElseThrow(() ->
                new ResourceNotFoundException(
                    "Source not found: " + id
                )
            );
    }
}
