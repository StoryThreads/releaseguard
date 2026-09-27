package com.releaseguard.analyzer;

import com.releaseguard.domain.ChangeSnapshot;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

@Component
public class TestImpactAnalyzer implements Analyzer {

    private static final String RULE_TEST_IMPACT = "TEST-001";

    @Override
    public AnalyzerType getType() {
        return AnalyzerType.TEST_IMPACT;
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

        List<ChangeSnapshot.ChangedFile> changedFiles =
            snapshot.getChangedFiles();

        Set<String> changedFilenames = new HashSet<>();

        for (ChangeSnapshot.ChangedFile file : changedFiles) {

            if (file == null || file.getFilename() == null) {
                continue;
            }

            changedFilenames.add(file.getFilename());
        }

        for (ChangeSnapshot.ChangedFile file : changedFiles) {

            if (file == null || file.getFilename() == null) {
                continue;
            }

            String filename = file.getFilename();

            if (!isProductionJavaFile(filename)) {
                continue;
            }

            String expectedTestFile = getExpectedTestFile(filename);

            if (!changedFilenames.contains(expectedTestFile)) {

                findings.add(new Finding(
                    AnalyzerType.TEST_IMPACT,
                    FindingType.TEST_IMPACT,
                    FindingSeverity.MEDIUM,
                    RULE_TEST_IMPACT,
                    "Test coverage may need updating",
                    "Production code changed without a corresponding test file change.",
                    filename,
                    null
                ));
            }
        }

        return findings;
    }

    private boolean isProductionJavaFile(String filename) {

        return filename.startsWith("src/main/java/")
            && filename.endsWith(".java");
    }

    private String getExpectedTestFile(String productionFile) {

        return productionFile
            .replace(
                "src/main/java/",
                "src/test/java/"
            )
            .replace(
                ".java",
                "Test.java"
            );
    }
}
