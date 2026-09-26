package com.releaseguard.entity;

import jakarta.persistence.*;

import java.time.OffsetDateTime;

@Entity
@Table(
    name = "changes",
    uniqueConstraints = {
        @UniqueConstraint(
            name = "uk_changes_external_id",
            columnNames = {
                "source_id",
                "external_change_id"
            }
        )
    }
)
public class Change {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(
        name = "source_id",
        nullable = false,
        foreignKey = @ForeignKey(name = "fk_changes_source")
    )
    private Source source;

    @Column(name = "external_change_id", nullable = false, length = 100)
    private String externalChangeId;

    @Column(nullable = false, length = 500)
    private String title;

    @Column(nullable = false, length = 200)
    private String author;

    @Column(name = "base_revision", nullable = false, length = 100)
    private String baseRevision;

    @Column(name = "head_revision", nullable = false, length = 100)
    private String headRevision;

    @Column(nullable = false, length = 30)
    private String status;

    @Column(name = "created_at", nullable = false)
    private OffsetDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private OffsetDateTime updatedAt;

    @PrePersist
    protected void onCreate() {
        OffsetDateTime now = OffsetDateTime.now();
        createdAt = now;
        updatedAt = now;
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = OffsetDateTime.now();
    }

    public Change() {
    }

    public Long getId() {
        return id;
    }

    public Source getSource() {
        return source;
    }

    public String getExternalChangeId() {
        return externalChangeId;
    }

    public String getTitle() {
        return title;
    }

    public String getAuthor() {
        return author;
    }

    public String getBaseRevision() {
        return baseRevision;
    }

    public String getHeadRevision() {
        return headRevision;
    }

    public String getStatus() {
        return status;
    }

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }

    public OffsetDateTime getUpdatedAt() {
        return updatedAt;
    }

    public void setSource(Source source) {
        this.source = source;
    }

    public void setExternalChangeId(String externalChangeId) {
        this.externalChangeId = externalChangeId;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public void setAuthor(String author) {
        this.author = author;
    }

    public void setBaseRevision(String baseRevision) {
        this.baseRevision = baseRevision;
    }

    public void setHeadRevision(String headRevision) {
        this.headRevision = headRevision;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public void setCreatedAt(OffsetDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public void setUpdatedAt(OffsetDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }
}
