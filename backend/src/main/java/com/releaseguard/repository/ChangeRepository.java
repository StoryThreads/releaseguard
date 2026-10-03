package com.releaseguard.repository;

import com.releaseguard.entity.Change;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface ChangeRepository extends JpaRepository<Change, Long> {

    List<Change> findBySourceId(Long sourceId);

    List<Change> findBySourceIdOrderByCreatedAtDesc(Long sourceId);

    List<Change> findAllByOrderByCreatedAtDesc();

    List<Change> findBySourceProjectIdOrderByCreatedAtDesc(Long projectId);

    Optional<Change> findBySourceIdAndExternalChangeId(
        Long sourceId,
        String externalChangeId
    );

    boolean existsBySourceIdAndExternalChangeId(
        Long sourceId,
        String externalChangeId
    );
}
