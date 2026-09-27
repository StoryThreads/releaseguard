package com.releaseguard.github;

import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class GitHubRestAdapterTest {

    @Autowired
    private GitHubRestAdapter githubRestAdapter;

    @Test
    void shouldGetAuthenticatedGitHubUser() {

        String response = githubRestAdapter.getAuthenticatedUser();

        assertNotNull(response);
        assertTrue(response.contains("\"login\""));
    }
}