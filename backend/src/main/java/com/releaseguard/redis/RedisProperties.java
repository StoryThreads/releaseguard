package com.releaseguard.redis;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Component
@ConfigurationProperties(prefix = "releaseguard.redis")
public class RedisProperties {

    private boolean enabled = true;
    private Ttls ttls = new Ttls();
    private RateLimiter rateLimiter = new RateLimiter();

    public boolean isEnabled() {
        return enabled;
    }

    public void setEnabled(boolean enabled) {
        this.enabled = enabled;
    }

    public Ttls getTtls() {
        return ttls;
    }

    public void setTtls(Ttls ttls) {
        this.ttls = ttls;
    }

    public RateLimiter getRateLimiter() {
        return rateLimiter;
    }

    public void setRateLimiter(RateLimiter rateLimiter) {
        this.rateLimiter = rateLimiter;
    }

    public static class Ttls {
        private long idempotencyProcessingSeconds = 300L;
        private long idempotencyCompletedSeconds = 86400L;
        private long githubDiffSeconds = 3600L;
        private long predictionResultSeconds = 86400L;

        public long getIdempotencyProcessingSeconds() {
            return idempotencyProcessingSeconds;
        }

        public void setIdempotencyProcessingSeconds(long idempotencyProcessingSeconds) {
            this.idempotencyProcessingSeconds = idempotencyProcessingSeconds;
        }

        public long getIdempotencyCompletedSeconds() {
            return idempotencyCompletedSeconds;
        }

        public void setIdempotencyCompletedSeconds(long idempotencyCompletedSeconds) {
            this.idempotencyCompletedSeconds = idempotencyCompletedSeconds;
        }

        public long getGithubDiffSeconds() {
            return githubDiffSeconds;
        }

        public void setGithubDiffSeconds(long githubDiffSeconds) {
            this.githubDiffSeconds = githubDiffSeconds;
        }

        public long getPredictionResultSeconds() {
            return predictionResultSeconds;
        }

        public void setPredictionResultSeconds(long predictionResultSeconds) {
            this.predictionResultSeconds = predictionResultSeconds;
        }
    }

    public static class RateLimiter {
        private boolean enabled = false;
        private int requestsPerMinute = 60;

        public boolean isEnabled() {
            return enabled;
        }

        public void setEnabled(boolean enabled) {
            this.enabled = enabled;
        }

        public int getRequestsPerMinute() {
            return requestsPerMinute;
        }

        public void setRequestsPerMinute(int requestsPerMinute) {
            this.requestsPerMinute = requestsPerMinute;
        }
    }
}
