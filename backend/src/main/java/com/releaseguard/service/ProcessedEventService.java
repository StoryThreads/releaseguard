package com.releaseguard.service;

import com.releaseguard.entity.ProcessedEvent;
import com.releaseguard.repository.ProcessedEventRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ProcessedEventService {

    private final ProcessedEventRepository repository;

    public ProcessedEventService(
        ProcessedEventRepository repository
    ) {
        this.repository = repository;
    }

    @Transactional
    public boolean isCompleted(String eventId) {

        return repository.findById(eventId)
            .map(event ->
                "COMPLETED".equals(event.getStatus())
            )
            .orElse(false);
    }

    @Transactional
    public void markProcessing(
        String eventId,
        String eventType,
        String correlationId
    ) {

        if (!repository.existsById(eventId)) {

            repository.save(
                new ProcessedEvent(
                    eventId,
                    eventType,
                    correlationId
                )
            );
        }
    }

    @Transactional
    public void markCompleted(String eventId) {

        ProcessedEvent event =
            repository.findById(eventId)
                .orElseThrow(() ->
                    new IllegalStateException(
                        "Processed event not found: " + eventId
                    )
                );

        event.markCompleted();

        repository.save(event);
    }
}
