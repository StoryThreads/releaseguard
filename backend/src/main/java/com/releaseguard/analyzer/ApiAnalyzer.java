package com.releaseguard.analyzer;

import com.releaseguard.domain.ChangeSnapshot;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Pattern;

@Component
public class ApiAnalyzer implements Analyzer {

    private static final String RULE_API_CHANGE = "API-001";

    private static final Pattern API_MAPPING_PATTERN = Pattern.compile(
        "@(?:GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\\b"
    );

    @Override
    public AnalyzerType getType() {
        return AnalyzerType.API;
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

            if (!isJavaFile(filename)) {
                continue;
            }

            if (containsApiMappingChange(patch)) {

                findings.add(new Finding(
                    AnalyzerType.API,
                    FindingType.API_ISSUE,
                    FindingSeverity.MEDIUM,
                    RULE_API_CHANGE,
                    "API endpoint change detected",
                    "A Spring API mapping was changed in the pull request.",
                    filename,
                    null
                ));
            }
        }

        return findings;
    }

    private boolean isJavaFile(String filename) {
        return filename.endsWith(".java");
    }

    private boolean containsApiMappingChange(String patch) {

        return patch.lines()
            .filter(line ->
                (line.startsWith("+") && !line.startsWith("+++"))
                    || (line.startsWith("-") && !line.startsWith("---"))
            )
            .map(line -> line.substring(1))
            .anyMatch(line -> API_MAPPING_PATTERN.matcher(line).find());
    }
}
