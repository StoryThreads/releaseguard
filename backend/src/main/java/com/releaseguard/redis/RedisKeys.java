package com.releaseguard.redis;

public final class RedisKeys {

    private RedisKeys() {
    }

    public static String idempotency(String eventId) {
        return "idemp:event:" + eventId;
    }

    public static String gitHubPr(String owner, String repo, long prNumber, String headSha) {
        return "gh:pr:" + owner + ":" + repo + ":" + prNumber + ":" + headSha;
    }

    public static String gitHubFiles(String owner, String repo, String commitSha) {
        return "gh:files:" + owner + ":" + repo + ":" + commitSha;
    }

    public static String analysisResult(Long projectId, String commitSha, String rulesetVersion) {
        return "analysis:" + projectId + ":" + commitSha + ":" + rulesetVersion;
    }

    public static String predictionResult(String commitSha, String modelVersion) {
        return "prediction:" + commitSha + ":" + modelVersion;
    }

    public static String rateLimit(String key) {
        return "ratelimit:" + key;
    }
}
