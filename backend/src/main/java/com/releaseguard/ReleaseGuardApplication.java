package com.releaseguard;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@ConfigurationPropertiesScan
public class ReleaseGuardApplication {

	public static void main(String[] args) {
		SpringApplication.run(ReleaseGuardApplication.class, args);
	}
}