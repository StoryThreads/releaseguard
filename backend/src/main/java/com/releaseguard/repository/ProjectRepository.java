package com.releaseguard.repository;

import com.releaseguard.entity.Project;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ProjectRepository extends JpaRepository<Project, Long> {

    boolean existsByName(String name);

    java.util.Optional<Project> findByName(String name);
}
