# V0.6 — Redis + Pipeline Hardening Architecture & Specification

## 1. Architectural Authority & Invariant Rules
1. **PostgreSQL is Authoritative**: Persistent business state (`projects`, `sources`, `changes`, `findings`, `ml_predictions`, `processed_events`) is permanently recorded in PostgreSQL. Redis is never the single point of truth.
2. **Kafka is the Event Delivery Backbone**: Kafka handles delivery, partitioning, and consumer group offsets.
3. **Redis is the Transient Coordination & Optimization Layer**:
   - Fast-path duplicate short-circuiting.
   - Atomic distributed lease acquisition (`SETNX`) with worker-specific tokens (`PROCESSING:<token>`) to prevent race conditions and concurrent duplicate execution.
   - Atomic lease release and completion via Redis Lua scripts ensuring that expired/reacquired leases are never wiped by a stalled worker.
   - Caching of heavy external roundtrips (GitHub files/diff and ML risk predictions).
   - Optional fixed-window rate limiting capability.
4. **Resilience / Fail-Open Principle**:
   - If Redis is down, unreachable, or times out, the pipeline **fails open** gracefully.
   - Idempotency falls back to PostgreSQL `ProcessedEventService`.
   - Caching falls back to direct API and computation calls.
   - Consumers never crash or drop events due to Redis unavailability.

---

## 2. Key Structure & TTL Strategy

### A. Currently Active Caches & TTLs (Implemented in V0.6)
Every configured TTL in `application.yml` directly corresponds to active caching in the codebase:

| Type | Key Pattern | TTL | Invalidation / Revalidation Policy |
| :--- | :--- | :--- | :--- |
| **Kafka In-Flight Lease** | `idemp:event:{eventId}` (value: `PROCESSING:<token>`) | 5 minutes (300s) | Leased atomically via `SETNX`. Released via Lua script matching token on exception. |
| **Kafka Completed Event** | `idemp:event:{eventId}` (value: `COMPLETED`) | 24 hours (86400s) | Natural expiry after 24h. Authoritative copy persists in PostgreSQL. |
| **GitHub PR Files / Diff** | `gh:files:{owner}:{repo}:{commitSha}` | 1 hour (3600s) | Key bound to immutable `commitSha` (`headRevision`). Pushing a new commit produces a new key naturally. |
| **ML Risk Prediction** | `prediction:{commitSha}:{modelVersion}` | 24 hours (86400s) | Key bound to commit SHA and configured ML model version (`releaseguard.ml-service.model-version`, e.g. `2.0.0`). Prevents stale inference cache across model deployments without code changes. |

### B. Planned Cache Namespaces (Reserved for Future Optimizations)
These namespaces are defined in `RedisKeys` for future architectural expansion, but are intentionally not active in V0.6 to avoid premature caching overhead:
- **GitHub PR Metadata** (`gh:pr:{owner}:{repo}:{prNumber}:{headSha}`): Reserved for caching PR title/author metadata if PR polling volume necessitates it. Currently, PR metadata is fetched fresh per event to resolve the latest `headSha`.
- **Analysis Results** (`analysis:{projectId}:{commitSha}:{rulesetVersion}`): Reserved for end-to-end analysis payload caching across identical ruleset versions.

### C. Rate Limiting Capability (Opt-In)
- **Rate Limiter Window** (`ratelimit:{actionKey}`, TTL 60s): Implemented as a **Redis fixed 1-minute window counter**.
- **Operational Status**: Implemented as an opt-in infrastructure capability (`RedisRateLimiter`), disabled by default (`releaseguard.redis.rate-limiter.enabled: false`), and not currently enforced on production request paths.

---

## 3. Distributed Lease Token Ownership & Lua Scripts

To prevent lease race conditions where Worker A hangs > 5 minutes, lease expires, Worker B acquires the lease, and Worker A resumes and wipes Worker B's active lease, all lease operations are tokenized and executed atomically via Lua scripts.

### Atomic Release Script:
```lua
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
else
    return 0
end
```

### Atomic Completion Script:
```lua
if redis.call('get', KEYS[1]) == ARGV[1] then
    redis.call('set', KEYS[1], 'COMPLETED', 'EX', ARGV[2])
    return 1
else
    return 0
end
```

### Kafka Acknowledgment & IN_PROGRESS Retry Handling:
When an event arrives and `acquireProcessingLease` returns `IN_PROGRESS`, it indicates that another worker currently holds an active lease for this `eventId`.
- **No Silent Dropping**: The consumer throws `EventProcessingInProgressException` instead of silently returning. This ensures the Kafka consumer does **not** commit the offset as successfully handled.
- **Retry with Backoff**: Spring Kafka's `DefaultErrorHandler` catches `EventProcessingInProgressException` and retries with backoff (`2000ms`, up to 3 attempts via `setBackOffFunction`).
- **Worker Crash Resilience**: If Worker A crashes midway, Worker B or redeliveries will not prematurely acknowledge the message. If retries are exhausted before the lease expires, the event is routed safely to `releaseguard.analysis.request.DLQ` rather than permanently disappearing.

### Idempotency State Machine:
```
               Incoming Kafka Event
                         │
                         ▼
        ┌──────────────────────────────────┐
        │  redisIdempotencyService         │
        │  .acquireProcessingLease(id)     │
        │  -> generates unique leaseToken  │
        └────────────────┬─────────────────┘
                         │
         ┌───────────────┼───────────────┬─────────────────────────┐
         ▼               ▼               ▼                         ▼
   [ ACQUIRED ]  [ IN_PROGRESS ] [ ALREADY_COMPLETED ]       [ FALLBACK ]
  (has leaseToken)       │               │                   (Redis Down)
         │         Throw           Acknowledge &                   │
         │     EventProcessing-    Short-Circuit                   │
         │     InProgressException (Duplicate Event                │
         │     (Kafka Retries/DLQ)  completed)                     │
         ▼                                                         ▼
   ┌─────────────┐                                           ┌─────────────┐
   │ Check DB    │                                           │ Check DB    │
   │ (Postgres)  │                                           │ (Postgres)  │
   └──────┬──────┘                                           └──────┬──────┘
          │                                                         │
          ▼                                                         ▼
   ┌─────────────┐                                           ┌─────────────┐
   │ Run Analysis│                                           │ Run Analysis│
   │ & Inference │                                           │ & Inference │
   └──────┬──────┘                                           └──────┬──────┘
          │                                                         │
    ┌─────┴────────────────┐                                        │
    │                      │                                        │
Success                 Failure                                     ▼
    │                      │                                 Mark Postgres
    ▼                      ▼                                 Completed
Mark Redis (Lua) &     Release Redis
Postgres Completed     Lease with Token
```

---

## 4. Configuration Reference

```yaml
spring:
  data:
    redis:
      host: ${REDIS_HOST:localhost}
      port: ${REDIS_PORT:6379}
      timeout: 2s
      connect-timeout: 2s

releaseguard:
  ml-service:
    url: ${ML_SERVICE_URL:http://localhost:8000}
    model-version: ${ML_MODEL_VERSION:2.0.0}
  redis:
    enabled: ${REDIS_ENABLED:true}
    ttls:
      idempotency-processing-seconds: 300
      idempotency-completed-seconds: 86400
      github-diff-seconds: 3600
      prediction-result-seconds: 86400
    rate-limiter:
      enabled: ${REDIS_RATE_LIMITER_ENABLED:false}
      requests-per-minute: 60
```

---

## 5. Verification & Test Suite

The implementation is validated by automated unit tests and real infrastructure integration tests:
1. `RedisKeysTest`: Verifies key formats, immutable SHA scoping, and model versioning.
2. `RedisIdempotencyServiceTest`: Tests tokenized lease acquisition (`ACQUIRED`), duplicate rejection, atomic Lua script lease release, atomic Lua script markCompleted, and fail-open fallback.
3. `RedisCacheServiceTest`: Tests JSON serialization/deserialization, generic type references, cache misses, evictions, and connection failure handling.
4. `RedisRateLimiterTest`: Tests fixed-window rate limiting, threshold enforcement, and fail-open behavior.
5. `PipelineHardeningTest`: Simulates Kafka event lifecycle, duplicate concurrent events, analysis exceptions with tokenized lease recovery, Redis outage fallback to PostgreSQL, and PostgreSQL-to-Redis state synchronization.
6. `AnalysisServiceTest`: Validates that cached GitHub files and cached ML predictions bypass external network roundtrips while persisting results authoritatively in PostgreSQL, and verifies that the prediction cache key respects the dynamically configured `releaseguard.ml-service.model-version`.
7. `RedisInfrastructureRestartIntegrationTest` (Real Redis Server Integration):
   - **Token ownership under expiration**: Worker A acquires lease -> lease expires after 1s -> Worker B acquires lease -> Worker A wakes up and attempts release -> Lua script rejects Worker A and leaves Worker B's lease active in Redis.
   - **Server crash & recovery**: Real Redis server stopped -> fail-open verified -> Redis server restarted on the same port -> connection re-established and operations resume successfully.
   - **Real duplicate short-circuit**: Completed event in real Redis immediately returns `ALREADY_COMPLETED` for duplicate arrivals.
