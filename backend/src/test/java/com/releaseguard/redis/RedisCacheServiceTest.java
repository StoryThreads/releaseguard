package com.releaseguard.redis;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.redis.RedisConnectionFailureException;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ValueOperations;

import java.time.Duration;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class RedisCacheServiceTest {

    @Mock
    private StringRedisTemplate redisTemplate;

    @Mock
    private ValueOperations<String, String> valueOperations;

    private ObjectMapper objectMapper;
    private RedisProperties properties;
    private RedisCacheService cacheService;

    record SamplePayload(String name, int score) {}

    @BeforeEach
    void setUp() {
        objectMapper = new ObjectMapper();
        properties = new RedisProperties();
        properties.setEnabled(true);
        cacheService = new RedisCacheService(redisTemplate, objectMapper, properties);
    }

    @Test
    void shouldPutAndGetSerializedObject() {
        when(redisTemplate.opsForValue()).thenReturn(valueOperations);

        SamplePayload payload = new SamplePayload("risk-analyzer", 95);
        boolean putSuccess = cacheService.put("test:key", payload, Duration.ofMinutes(10));

        assertTrue(putSuccess);
        verify(valueOperations).set(eq("test:key"), eq("{\"name\":\"risk-analyzer\",\"score\":95}"), eq(Duration.ofMinutes(10)));

        when(valueOperations.get("test:key")).thenReturn("{\"name\":\"risk-analyzer\",\"score\":95}");

        Optional<SamplePayload> cached = cacheService.get("test:key", SamplePayload.class);
        assertTrue(cached.isPresent());
        assertEquals("risk-analyzer", cached.get().name());
        assertEquals(95, cached.get().score());
    }

    @Test
    void shouldReturnEmptyOnCacheMiss() {
        when(redisTemplate.opsForValue()).thenReturn(valueOperations);
        when(valueOperations.get("test:missing")).thenReturn(null);

        Optional<SamplePayload> cached = cacheService.get("test:missing", SamplePayload.class);
        assertTrue(cached.isEmpty());
    }

    @Test
    void shouldSupportGenericTypeReference() {
        when(redisTemplate.opsForValue()).thenReturn(valueOperations);
        when(valueOperations.get("test:list")).thenReturn("[\"file1.java\",\"file2.java\"]");

        Optional<List<String>> cached = cacheService.get("test:list", new TypeReference<List<String>>() {});
        assertTrue(cached.isPresent());
        assertEquals(2, cached.get().size());
        assertEquals("file1.java", cached.get().get(0));
    }

    @Test
    void shouldEvictKey() {
        when(redisTemplate.delete("test:key")).thenReturn(Boolean.TRUE);

        boolean evicted = cacheService.evict("test:key");
        assertTrue(evicted);
        verify(redisTemplate).delete("test:key");
    }

    @Test
    void shouldFailOpenGracefullyWhenRedisThrows() {
        when(redisTemplate.opsForValue()).thenReturn(valueOperations);
        when(valueOperations.get(any()))
                .thenThrow(new RedisConnectionFailureException("Redis connection timed out"));

        Optional<SamplePayload> cached = cacheService.get("test:error", SamplePayload.class);
        assertTrue(cached.isEmpty());

        doThrow(new RedisConnectionFailureException("Redis write timed out"))
                .when(valueOperations).set(any(), any(), any(Duration.class));

        boolean putSuccess = cacheService.put("test:error", new SamplePayload("fail", 0), Duration.ofMinutes(5));
        assertFalse(putSuccess);
    }
}
