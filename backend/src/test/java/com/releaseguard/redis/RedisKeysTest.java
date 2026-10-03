package com.releaseguard.redis;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class RedisKeysTest {

    @Test
    void shouldFormatIdempotencyKey() {
        String key = RedisKeys.idempotency("evt-12345");
        assertEquals("idemp:event:evt-12345", key);
    }

    @Test
    void shouldFormatGitHubPrKeyWithImmutableHeadSha() {
        String key = RedisKeys.gitHubPr("StoryThreads", "releaseguard", 42L, "abc1234");
        assertEquals("gh:pr:StoryThreads:releaseguard:42:abc1234", key);
    }

    @Test
    void shouldFormatGitHubFilesKeyWithImmutableCommitSha() {
        String key = RedisKeys.gitHubFiles("StoryThreads", "releaseguard", "def5678");
        assertEquals("gh:files:StoryThreads:releaseguard:def5678", key);
    }

    @Test
    void shouldFormatAnalysisResultKeyWithRulesetVersion() {
        String key = RedisKeys.analysisResult(101L, "abc1234", "v1.2.0");
        assertEquals("analysis:101:abc1234:v1.2.0", key);
    }

    @Test
    void shouldFormatPredictionResultKeyWithModelVersion() {
        String key = RedisKeys.predictionResult("abc1234", "2.0.0");
        assertEquals("prediction:abc1234:2.0.0", key);
    }

    @Test
    void shouldFormatRateLimitKey() {
        String key = RedisKeys.rateLimit("github:api");
        assertEquals("ratelimit:github:api", key);
    }
}
