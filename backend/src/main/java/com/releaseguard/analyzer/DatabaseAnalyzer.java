package com.releaseguard.analyzer;

import com.releaseguard.domain.ChangeSnapshot;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Pattern;

@Component
public class DatabaseAnalyzer implements Analyzer {

    private static final String RULE_DATABASE_CHANGE = "DB-001";

    private static final Pattern DATABASE_CHANGE_PATTERN = Pattern.compile(
        "\\b(CREATE|ALTER|DROP)\\s+"
            + "(TABLE|INDEX|VIEW)\\b",
        Pattern.CASE_INSENSITIVE
    );

    @Override
    public AnalyzerType getType() {
        return AnalyzerType.DATABASE;
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

            if (!isDatabaseFile(filename)) {
                continue;
            }

            if (containsDatabaseChange(patch)) {

                findings.add(new Finding(
                    AnalyzerType.DATABASE,
                    FindingType.DATABASE_ISSUE,
                    FindingSeverity.MEDIUM,
                    RULE_DATABASE_CHANGE,
                    "Database schema change detected",
                    "A database schema change was detected in the pull request.",
                    filename,
                    null
                ));
            }
        }

        return findings;
    }

    private boolean isDatabaseFile(String filename) {

        return filename.endsWith(".sql");
    }

    private boolean containsDatabaseChange(String patch) {

        return patch.lines()
            .filter(line ->
                (line.startsWith("+") && !line.startsWith("+++"))
                    || (line.startsWith("-") && !line.startsWith("---"))
            )
            .map(line -> line.substring(1))
            .anyMatch(line ->
                DATABASE_CHANGE_PATTERN.matcher(line).find()
            );
    }
}
