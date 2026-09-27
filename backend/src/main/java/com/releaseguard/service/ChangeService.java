package com.releaseguard.service;

import com.releaseguard.entity.Change;
import com.releaseguard.entity.Source;
import com.releaseguard.exception.ConflictException;
import com.releaseguard.exception.ResourceNotFoundException;
import com.releaseguard.repository.ChangeRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@Transactional
public class ChangeService {

    private final ChangeRepository changeRepository;
    private final SourceService sourceService;

    public ChangeService(
        ChangeRepository changeRepository,
        SourceService sourceService
    ) {
        this.changeRepository = changeRepository;
        this.sourceService = sourceService;
    }

    public Change createChange(
        Long sourceId,
        String externalChangeId,
        String title,
        String author,
        String baseRevision,
        String headRevision,
        String status
    ) {

        Source source = sourceService.getSource(sourceId);

        if (changeRepository.existsBySourceIdAndExternalChangeId(
            sourceId,
            externalChangeId
        )) {
            throw new ConflictException(
                "Change already exists for this source"
            );
        }

        Change change = new Change();

        change.setSource(source);
        change.setExternalChangeId(externalChangeId);
        change.setTitle(title);
        change.setAuthor(author);
        change.setBaseRevision(baseRevision);
        change.setHeadRevision(headRevision);
        change.setStatus(status);

        return changeRepository.save(change);
    }

    public Change getOrCreateChange(
        Long sourceId,
        String externalChangeId,
        String title,
        String author,
        String baseRevision,
        String headRevision,
        String status
    ) {

        Source source = sourceService.getSource(sourceId);

        Change change = changeRepository
            .findBySourceIdAndExternalChangeId(sourceId, externalChangeId)
            .orElseGet(Change::new);

        change.setSource(source);
        change.setExternalChangeId(externalChangeId);
        change.setTitle(title);
        change.setAuthor(author);
        change.setBaseRevision(baseRevision);
        change.setHeadRevision(headRevision);
        change.setStatus(status);

        return changeRepository.save(change);
    }

    @Transactional(readOnly = true)
    public List<Change> getChangesBySource(Long sourceId) {

        sourceService.getSource(sourceId);

        return changeRepository.findBySourceId(sourceId);
    }

    @Transactional(readOnly = true)
    public Change getChange(Long id) {

        return changeRepository.findById(id)
            .orElseThrow(() ->
                new ResourceNotFoundException(
                    "Change not found: " + id
                )
            );
    }
}
