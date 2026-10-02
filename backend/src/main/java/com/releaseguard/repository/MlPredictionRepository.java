package com.releaseguard.repository;

import com.releaseguard.entity.MlPredictionEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface MlPredictionRepository
    extends JpaRepository<MlPredictionEntity, Long> {

    Optional<MlPredictionEntity> findByChangeId(Long changeId);
}
