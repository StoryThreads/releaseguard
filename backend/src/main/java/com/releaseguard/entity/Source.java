package com.releaseguard.entity;

import jakarta.persistence.*;

import java.time.OffsetDateTime;

@Entity
@Table(
    name = "sources",
    uniqueConstraints = {
        @UniqueConstraint(
            name = "uk_sources_repository",
            columnNames = {
                "project_id",
                "provider",
                "repository_owner",
                "repository_name"
            }
        )
    }
)
public class Source {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(
        name = "project_id",
        nullable = false,
        foreignKey = @ForeignKey(name = "fk_sources_project")
    )
    private Project project;

    @Column(nullable = false, length = 30)
    private String provider;

    @Column(name = "repository_owner", nullable = false, length = 100)
    private String repositoryOwner;

    @Column(name = "repository_name", nullable = false, length = 200)
    private String repositoryName;

    @Column(name = "default_branch", nullable = false, length = 100)
    private String defaultBranch;

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

    public Source() {
    }

    public Long getId() {
        return id;
    }

    public Project getProject() {
        return project;
    }

    public String getProvider() {
        return provider;
    }

    public String getRepositoryOwner() {
        return repositoryOwner;
    }

    public String getRepositoryName() {
        return repositoryName;
    }

    public String getDefaultBranch() {
        return defaultBranch;
    }

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }

    public OffsetDateTime getUpdatedAt() {
        return updatedAt;
    }

    public void setProject(Project project) {
        this.project = project;
    }

    public void setProvider(String provider) {
        this.provider = provider;
    }

    public void setRepositoryOwner(String repositoryOwner) {
        this.repositoryOwner = repositoryOwner;
    }

    public void setRepositoryName(String repositoryName) {
        this.repositoryName = repositoryName;
    }

    public void setDefaultBranch(String defaultBranch) {
        this.defaultBranch = defaultBranch;
    }

    public void setCreatedAt(OffsetDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public void setUpdatedAt(OffsetDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }
}
