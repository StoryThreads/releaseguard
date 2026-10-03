package com.releaseguard.webhook;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

@Component
public class WebhookSignatureVerifier {

    private static final Logger log = LoggerFactory.getLogger(WebhookSignatureVerifier.class);
    private static final String HMAC_SHA256 = "HmacSHA256";

    private final String webhookSecret;

    public WebhookSignatureVerifier(
        @Value("${github.webhook-secret:releaseguard-webhook-secret-dev}") String webhookSecret
    ) {
        this.webhookSecret = webhookSecret != null ? webhookSecret.trim() : "";
    }

    public boolean isValid(byte[] payloadBytes, String signatureHeader) {
        if (webhookSecret.isEmpty()) {
            log.warn("GitHub webhook secret is not configured; skipping signature verification");
            return true;
        }

        if (signatureHeader == null || !signatureHeader.startsWith("sha256=")) {
            log.warn("Missing or malformed X-Hub-Signature-256 header: {}", signatureHeader);
            return false;
        }

        String expectedHash = signatureHeader.substring("sha256=".length()).trim();

        try {
            Mac mac = Mac.getInstance(HMAC_SHA256);
            SecretKeySpec secretKey = new SecretKeySpec(
                webhookSecret.getBytes(StandardCharsets.UTF_8),
                HMAC_SHA256
            );
            mac.init(secretKey);

            byte[] hmacBytes = mac.doFinal(payloadBytes);
            StringBuilder hexString = new StringBuilder();
            for (byte b : hmacBytes) {
                String hex = Integer.toHexString(0xff & b);
                if (hex.length() == 1) {
                    hexString.append('0');
                }
                hexString.append(hex);
            }
            String actualHash = hexString.toString();

            // Constant-time comparison to prevent timing attacks
            return MessageDigest.isEqual(
                actualHash.getBytes(StandardCharsets.UTF_8),
                expectedHash.getBytes(StandardCharsets.UTF_8)
            );
        } catch (Exception e) {
            log.error("Failed to calculate HMAC-SHA256 signature for webhook: {}", e.getMessage());
            return false;
        }
    }
}
