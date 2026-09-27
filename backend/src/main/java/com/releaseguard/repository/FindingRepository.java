package com.releaseguard.repository;

import com.releaseguard.entity.FindingEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface FindingRepository extends JpaRepository<FindingEntity, Long> {

    List<FindingEntity> findByChangeIdOrderByIdAsc(Long changeId);

    long countByChangeId(Long changeId);

    void deleteByChangeId(Long changeId);
}
