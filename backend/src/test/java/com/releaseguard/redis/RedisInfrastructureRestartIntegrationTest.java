package com.releaseguard.redis;

import io.lettuce.core.ClientOptions;
import io.lettuce.core.SocketOptions;
import io.lettuce.core.TimeoutOptions;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.data.redis.connection.RedisStandaloneConfiguration;
import org.springframework.data.redis.connection.lettuce.LettuceClientConfiguration;
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory;
import org.springframework.data.redis.core.StringRedisTemplate;
import redis.embedded.RedisServer;

import java.io.IOException;
import java.net.ServerSocket;
import java.time.Duration;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

class RedisInfrastructureRestartIntegrationTest {

    private int redisPort;
    private RedisServer redisServer;
    private LettuceConnectionFactory connectionFactory;
    private StringRedisTemplate redisTemplate;
    private RedisProperties properties;
    private RedisIdempotencyService idempotencyService;

    @BeforeEach
    void setUp() throws IOException {
        // Allocate a free ephemeral port
        try (ServerSocket socket = new ServerSocket(0)) {
            redisPort = socket.getLocalPort();
        }

        redisServer = RedisServer.newRedisServer()
                .port(redisPort)
                .build();
        redisServer.start();

        RedisStandaloneConfiguration serverConfig =
                new RedisStandaloneConfiguration("127.0.0.1", redisPort);

        ClientOptions clientOptions = ClientOptions.builder()
                .socketOptions(SocketOptions.builder().connectTimeout(Duration.ofMillis(500)).build())
                .timeoutOptions(TimeoutOptions.enabled())
                .disconnectedBehavior(ClientOptions.DisconnectedBehavior.REJECT_COMMANDS)
                .build();

        LettuceClientConfiguration clientConfig = LettuceClientConfiguration.builder()
                .commandTimeout(Duration.ofMillis(500))
                .clientOptions(clientOptions)
                .build();

        connectionFactory = new LettuceConnectionFactory(serverConfig, clientConfig);
        connectionFactory.afterPropertiesSet();

        redisTemplate = new StringRedisTemplate(connectionFactory);
        redisTemplate.afterPropertiesSet();

        properties = new RedisProperties();
        properties.setEnabled(true);
        properties.getTtls().setIdempotencyProcessingSeconds(2L); // 2 second short TTL for expiry test
        properties.getTtls().setIdempotencyCompletedSeconds(10L);

        idempotencyService = new RedisIdempotencyService(redisTemplate, properties);
    }

    @AfterEach
    void tearDown() {
        if (connectionFactory != null) {
            try {
                connectionFactory.destroy();
            } catch (Exception ignored) {
            }
        }
        if (redisServer != null && redisServer.isActive()) {
            try {
                redisServer.stop();
            } catch (Exception ignored) {
            }
        }
    }

    @Test
    void shouldPreventWorkerAFromDeletingWorkerBLeaseAfterExpiry() throws InterruptedException {
        String eventId = "evt-lease-expiry-test";

        // Step 1: Worker A acquires lease (TTL = 2 seconds)
        RedisIdempotencyService.LeaseResult workerAResult =
                idempotencyService.acquireProcessingLease(eventId);

        assertTrue(workerAResult.isAcquired());
        String workerAToken = workerAResult.leaseToken();
        assertNotNull(workerAToken);

        // Verify key is set in real Redis with Worker A's token
        String initialValue = redisTemplate.opsForValue().get(RedisKeys.idempotency(eventId));
        assertEquals(RedisIdempotencyService.STATUS_PROCESSING_PREFIX + workerAToken, initialValue);

        // Step 2: Worker A hangs while lease expires in real Redis (> 2 seconds)
        Thread.sleep(2200);

        // Step 3: Worker B picks up the expired task and acquires a new lease
        RedisIdempotencyService.LeaseResult workerBResult =
                idempotencyService.acquireProcessingLease(eventId);

        assertTrue(workerBResult.isAcquired());
        String workerBToken = workerBResult.leaseToken();
        assertNotNull(workerBToken);
        assertFalse(workerAToken.equals(workerBToken));

        String workerBValue = redisTemplate.opsForValue().get(RedisKeys.idempotency(eventId));
        assertEquals(RedisIdempotencyService.STATUS_PROCESSING_PREFIX + workerBToken, workerBValue);

        // Step 4: Worker A resumes and attempts to release the lease using Worker A's stale token
        boolean workerARelease =
                idempotencyService.releaseProcessingLease(eventId, workerAToken);

        // Must FAIL because Worker A no longer owns the active lease
        assertFalse(workerARelease);

        // Crucial Assertion: Worker B's active lease MUST REMAIN in real Redis
        String currentRedisValue = redisTemplate.opsForValue().get(RedisKeys.idempotency(eventId));
        assertEquals(RedisIdempotencyService.STATUS_PROCESSING_PREFIX + workerBToken, currentRedisValue);

        // Step 5: Worker A attempts to mark COMPLETED using stale token -> rejected by Lua script
        boolean workerAMarkCompleted =
                idempotencyService.markCompleted(eventId, workerAToken);
        assertFalse(workerAMarkCompleted);

        // Step 6: Worker B finishes successfully and releases its own lease
        boolean workerBRelease =
                idempotencyService.releaseProcessingLease(eventId, workerBToken);
        assertTrue(workerBRelease);
    }

    @Test
    void shouldHandleRealRedisCrashAndRecoveryGracefully() throws IOException {
        String eventId = "evt-redis-restart-test";

        // Step 1: Normal acquisition while Redis is running
        RedisIdempotencyService.LeaseResult firstResult =
                idempotencyService.acquireProcessingLease(eventId);
        assertTrue(firstResult.isAcquired());
        idempotencyService.releaseProcessingLease(eventId, firstResult.leaseToken());

        // Step 2: Simulate Redis crash (stop Redis server)
        redisServer.stop();

        // Step 3: During outage, acquireProcessingLease fails open without crashing
        RedisIdempotencyService.LeaseResult outageResult =
                idempotencyService.acquireProcessingLease(eventId);
        assertEquals(RedisIdempotencyService.LeaseStatus.FALLBACK, outageResult.status());
        assertFalse(outageResult.isAcquired());

        // Step 4: Simulate Redis recovery (restart Redis server on the same port)
        redisServer = RedisServer.newRedisServer()
                .port(redisPort)
                .build();
        redisServer.start();

        // Reset connection factory to re-establish channel after restart
        connectionFactory.resetConnection();

        // Step 5: After recovery, Redis operations resume successfully
        RedisIdempotencyService.LeaseResult recoveredResult =
                idempotencyService.acquireProcessingLease(eventId);

        assertTrue(recoveredResult.isAcquired());
        assertNotNull(recoveredResult.leaseToken());

        boolean completed =
                idempotencyService.markCompleted(eventId, recoveredResult.leaseToken());
        assertTrue(completed);
        assertTrue(idempotencyService.isCompleted(eventId));
    }

    @Test
    void shouldShortCircuitDuplicateEventInRealRedis() {
        String eventId = "evt-duplicate-shortcircuit";

        // First attempt acquires and completes
        RedisIdempotencyService.LeaseResult first =
                idempotencyService.acquireProcessingLease(eventId);
        assertTrue(first.isAcquired());

        boolean completed = idempotencyService.markCompleted(eventId, first.leaseToken());
        assertTrue(completed);

        // Second duplicate attempt receives ALREADY_COMPLETED
        RedisIdempotencyService.LeaseResult duplicate =
                idempotencyService.acquireProcessingLease(eventId);

        assertEquals(RedisIdempotencyService.LeaseStatus.ALREADY_COMPLETED, duplicate.status());
        assertFalse(duplicate.isAcquired());
    }
}
