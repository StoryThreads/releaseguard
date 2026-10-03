package com.releaseguard.redis;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.Optional;

@Service
public class RedisCacheService {

    private static final Logger log =
            LoggerFactory.getLogger(RedisCacheService.class);

    private final StringRedisTemplate redisTemplate;
    private final ObjectMapper objectMapper;
    private final RedisProperties properties;

    @Autowired
    public RedisCacheService(
            @org.springframework.lang.Nullable StringRedisTemplate redisTemplate,
            ObjectMapper objectMapper,
            RedisProperties properties
    ) {
        this.redisTemplate = redisTemplate;
        this.objectMapper = objectMapper;
        this.properties = properties;
    }

    public <T> Optional<T> get(String key, Class<T> clazz) {
        if (!properties.isEnabled() || redisTemplate == null) {
            return Optional.empty();
        }

        try {
            String json = redisTemplate.opsForValue().get(key);
            if (json == null || json.isBlank()) {
                return Optional.empty();
            }
            return Optional.of(objectMapper.readValue(json, clazz));
        } catch (Exception ex) {
            log.warn("Redis cache read failed for key={}. Falling back to source. Error: {}",
                    key, ex.getMessage());
            return Optional.empty();
        }
    }

    public <T> Optional<T> get(String key, TypeReference<T> typeReference) {
        if (!properties.isEnabled() || redisTemplate == null) {
            return Optional.empty();
        }

        try {
            String json = redisTemplate.opsForValue().get(key);
            if (json == null || json.isBlank()) {
                return Optional.empty();
            }
            return Optional.of(objectMapper.readValue(json, typeReference));
        } catch (Exception ex) {
            log.warn("Redis cache read failed for key={}. Falling back to source. Error: {}",
                    key, ex.getMessage());
            return Optional.empty();
        }
    }

    public <T> boolean put(String key, T value, Duration ttl) {
        if (!properties.isEnabled() || redisTemplate == null || value == null) {
            return false;
        }

        try {
            String json = objectMapper.writeValueAsString(value);
            redisTemplate.opsForValue().set(key, json, ttl);
            return true;
        } catch (Exception ex) {
            log.warn("Redis cache write failed for key={}. Error: {}",
                    key, ex.getMessage());
            return false;
        }
    }

    public boolean evict(String key) {
        if (!properties.isEnabled() || redisTemplate == null) {
            return false;
        }

        try {
            return Boolean.TRUE.equals(redisTemplate.delete(key));
        } catch (Exception ex) {
            log.warn("Redis cache evict failed for key={}. Error: {}",
                    key, ex.getMessage());
            return false;
        }
    }

    public boolean hasKey(String key) {
        if (!properties.isEnabled() || redisTemplate == null) {
            return false;
        }

        try {
            return Boolean.TRUE.equals(redisTemplate.hasKey(key));
        } catch (Exception ex) {
            log.warn("Redis hasKey check failed for key={}. Error: {}",
                    key, ex.getMessage());
            return false;
        }
    }
}
