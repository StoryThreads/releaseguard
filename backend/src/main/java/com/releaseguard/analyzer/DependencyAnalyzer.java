package com.releaseguard.analyzer;

import com.releaseguard.domain.ChangeSnapshot;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;

@Component
public class DependencyAnalyzer implements Analyzer {

    private static final String RULE_DEPENDENCY_CHANGE = "DEP-001";

    @Override
    public AnalyzerType getType() {
        return AnalyzerType.DEPENDENCY;
    }

    @Override
    public List<Finding> analyze(AnalyzerContext context) {

        List<Finding> findings = new ArrayList<>();

        if (context == null) {
            return findings;
        }

        ChangeSnapshot snapshot = context.changeSnapshot();

        if (snapshot == null || snapshot.getChangedFiles() == null) {
            return findings;
        }

        for (ChangeSnapshot.ChangedFile changedFile : snapshot.getChangedFiles()) {

            if (changedFile == null) {
                continue;
            }

            String filename = changedFile.getFilename();
            String patch = changedFile.getPatch();

            if (filename == null || patch == null || patch.isBlank()) {
                continue;
            }

            if (!isDependencyFile(filename)) {
                continue;
            }

            if (containsDependencyChange(patch)) {

                findings.add(new Finding(
                    AnalyzerType.DEPENDENCY,
                    FindingType.DEPENDENCY_ISSUE,
                    FindingSeverity.MEDIUM,
                    RULE_DEPENDENCY_CHANGE,
                    "Dependency change detected",
                    "A dependency change was detected in the pull request.",
                    filename,
                    null
                ));
            }
        }

        return findings;
    }

    private boolean isDependencyFile(String filename) {

        return filename.equals("pom.xml")
            || filename.equals("package.json")
            || filename.equals("build.gradle")
            || filename.equals("build.gradle.kts");
    }

    private boolean containsDependencyChange(String patch) {

        return patch.lines()
            .anyMatch(line ->
                (line.startsWith("+") && !line.startsWith("+++"))
                    || (line.startsWith("-") && !line.startsWith("---"))
            );
    }
}
