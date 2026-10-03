package com.releaseguard.dto.analysis;

import java.util.List;

public class ChangedFileResponse {
    private String filename;
    private String status;
    private int additions;
    private int deletions;
    private int changes;
    private String patch;
    private List<String> tags;

    public ChangedFileResponse() {
    }

    public ChangedFileResponse(
        String filename,
        String status,
        int additions,
        int deletions,
        int changes,
        String patch,
        List<String> tags
    ) {
        this.filename = filename;
        this.status = status;
        this.additions = additions;
        this.deletions = deletions;
        this.changes = changes;
        this.patch = patch;
        this.tags = tags != null ? tags : List.of();
    }

    public String getFilename() {
        return filename;
    }

    public void setFilename(String filename) {
        this.filename = filename;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public int getAdditions() {
        return additions;
    }

    public void setAdditions(int additions) {
        this.additions = additions;
    }

    public int getDeletions() {
        return deletions;
    }

    public void setDeletions(int deletions) {
        this.deletions = deletions;
    }

    public int getChanges() {
        return changes;
    }

    public void setChanges(int changes) {
        this.changes = changes;
    }

    public String getPatch() {
        return patch;
    }

    public void setPatch(String patch) {
        this.patch = patch;
    }

    public List<String> getTags() {
        return tags;
    }

    public void setTags(List<String> tags) {
        this.tags = tags;
    }
}
