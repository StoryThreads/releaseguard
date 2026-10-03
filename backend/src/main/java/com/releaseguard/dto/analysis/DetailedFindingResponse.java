package com.releaseguard.dto.analysis;

import java.time.OffsetDateTime;

public class DetailedFindingResponse {

    private Long id;
    private String analyzerType;
    private String findingType;
    private String severity;
    private String ruleId;
    private String title;
    private String message;
    private String filePath;
    private Integer lineNumber;
    private OffsetDateTime createdAt;

    public DetailedFindingResponse() {
    }

    public DetailedFindingResponse(
        Long id,
        String analyzerType,
        String findingType,
        String severity,
        String ruleId,
        String title,
        String message,
        String filePath,
        Integer lineNumber,
        OffsetDateTime createdAt
    ) {
        this.id = id;
        this.analyzerType = analyzerType;
        this.findingType = findingType;
        this.severity = severity;
        this.ruleId = ruleId;
        this.title = title;
        this.message = message;
        this.filePath = filePath;
        this.lineNumber = lineNumber;
        this.createdAt = createdAt;
    }

    public Long getId() {
        return id;
    }

    public String getAnalyzerType() {
        return analyzerType;
    }

    public String getFindingType() {
        return findingType;
    }

    public String getSeverity() {
        return severity;
    }

    public String getRuleId() {
        return ruleId;
    }

    public String getTitle() {
        return title;
    }

    public String getMessage() {
        return message;
    }

    public String getFilePath() {
        return filePath;
    }

    public Integer getLineNumber() {
        return lineNumber;
    }

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }
}
