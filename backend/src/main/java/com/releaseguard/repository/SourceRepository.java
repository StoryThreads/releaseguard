package com.releaseguard.repository;

import com.releaseguard.entity.Source;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface SourceRepository extends JpaRepository<Source, Long> {

    List<Source> findByProjectId(Long projectId);

    List<Source> findByProviderIgnoreCaseAndRepositoryOwnerIgnoreCaseAndRepositoryNameIgnoreCase(
        String provider,
        String repositoryOwner,
        String repositoryName
    );

    boolean existsByProjectIdAndProviderAndRepositoryOwnerAndRepositoryName(
        Long projectId,
        String provider,
        String repositoryOwner,
        String repositoryName
    );
}
