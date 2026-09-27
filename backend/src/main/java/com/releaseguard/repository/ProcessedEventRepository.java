package com.releaseguard.repository;

import com.releaseguard.entity.ProcessedEvent;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ProcessedEventRepository
    extends JpaRepository<ProcessedEvent, String> {

}
