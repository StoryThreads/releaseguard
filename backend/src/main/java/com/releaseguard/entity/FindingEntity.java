package com.releaseguard.entity;

import jakarta.persistence.*;

import java.time.OffsetDateTime;

@Entity
@Table(
    name = "findings",
    indexes = {
        @Index(name = "idx_findings_change_id", columnList = "change_id"),
        @Index(name = "idx_findings_severity", columnList = "severity"),
        @Index(name = "idx_findings_rule_id", columnList = "rule_id")
    }
)
public class FindingEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(
        name = "change_id",
        nullable = false,
        foreignKey = @ForeignKey(name = "fk_findings_change")
    )
    private Change change;

    @Column(name = "analyzer_type", nullable = false, length = 50)
    private String analyzerType;

    @Column(name = "finding_type", nullable = false, length = 50)
    private String findingType;

    @Column(nullable = false, length = 30)
    private String severity;

    @Column(name = "rule_id", nullable = false, length = 100)
    private String ruleId;

    @Column(nullable = false, length = 500)
    private String title;

    @Column(nullable = false, length = 2000)
    private String message;

    @Column(name = "file_path", length = 1000)
    private String filePath;

    @Column(name = "line_number")
    private Integer lineNumber;

    @Column(name = "created_at", nullable = false)
    private OffsetDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        if (createdAt == null) {
            createdAt = OffsetDateTime.now();
        }
    }

    public FindingEntity() {
    }

    public Long getId() {
        return id;
    }

    public Change getChange() {
        return change;
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

    public void setChange(Change change) {
        this.change = change;
    }

    public void setAnalyzerType(String analyzerType) {
        this.analyzerType = analyzerType;
    }

    public void setFindingType(String findingType) {
        this.findingType = findingType;
    }

    public void setSeverity(String severity) {
        this.severity = severity;
    }

    public void setRuleId(String ruleId) {
        this.ruleId = ruleId;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public void setFilePath(String filePath) {
        this.filePath = filePath;
    }

    public void setLineNumber(Integer lineNumber) {
        this.lineNumber = lineNumber;
    }

    public void setCreatedAt(OffsetDateTime createdAt) {
        this.createdAt = createdAt;
    }
}
