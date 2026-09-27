package com.releaseguard.service;

import com.releaseguard.analyzer.Finding;
import com.releaseguard.entity.Change;
import com.releaseguard.entity.FindingEntity;
import com.releaseguard.repository.FindingRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class FindingPersistenceService {

    private final FindingRepository findingRepository;

    public FindingPersistenceService(
        FindingRepository findingRepository
    ) {
        this.findingRepository = findingRepository;
    }

    @Transactional
    public List<FindingEntity> replaceFindings(
        Change change,
        List<Finding> findings
    ) {

        if (change == null) {
            return List.of();
        }

        if (change.getId() != null) {
            findingRepository.deleteByChangeId(change.getId());
        }

        if (findings == null || findings.isEmpty()) {
            return List.of();
        }

        List<FindingEntity> entities = findings.stream()
            .filter(finding -> finding != null)
            .map(finding -> toEntity(change, finding))
            .toList();

        return findingRepository.saveAll(entities);
    }

    @Transactional(readOnly = true)
    public List<FindingEntity> getFindings(Long changeId) {

        if (changeId == null) {
            return List.of();
        }

        return findingRepository.findByChangeIdOrderByIdAsc(changeId);
    }

    @Transactional(readOnly = true)
    public long countFindings(Long changeId) {

        if (changeId == null) {
            return 0;
        }

        return findingRepository.countByChangeId(changeId);
    }

    private FindingEntity toEntity(
        Change change,
        Finding finding
    ) {

        FindingEntity entity = new FindingEntity();

        entity.setChange(change);
        entity.setAnalyzerType(
            finding.analyzerType() == null
                ? null
                : finding.analyzerType().name()
        );

        entity.setFindingType(
            finding.findingType() == null
                ? null
                : finding.findingType().name()
        );

        entity.setSeverity(
            finding.severity() == null
                ? null
                : finding.severity().name()
        );

        entity.setRuleId(finding.ruleId());
        entity.setTitle(finding.title());
        entity.setMessage(finding.message());
        entity.setFilePath(finding.filePath());
        entity.setLineNumber(finding.lineNumber());

        return entity;
    }
}
