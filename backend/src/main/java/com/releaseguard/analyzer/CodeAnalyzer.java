package com.releaseguard.analyzer;

import com.releaseguard.domain.ChangeSnapshot;

import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Pattern;

@Component
public class CodeAnalyzer implements Analyzer {

    private static final String RULE_DEBUG_PRINT = "CODE-001";
    private static final String RULE_TODO = "CODE-002";
    private static final String RULE_EMPTY_CATCH = "CODE-003";

    private static final Pattern DEBUG_PRINT_PATTERN =
        Pattern.compile("\\bSystem\\.out\\.println\\s*\\(");

    private static final Pattern TODO_PATTERN =
        Pattern.compile("\\b(TODO|FIXME)\\b", Pattern.CASE_INSENSITIVE);

    private static final Pattern EMPTY_CATCH_PATTERN =
        Pattern.compile(
            "catch\\s*\\([^)]*\\)\\s*\\{\\s*}",
            Pattern.DOTALL
        );

    @Override
    public AnalyzerType getType() {
        return AnalyzerType.CODE;
    }

    @Override
    public List<Finding> analyze(AnalyzerContext context) {

        List<Finding> findings = new ArrayList<>();

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

            if (!isAnalyzableCodeFile(filename)) {
                continue;
            }

            analyzeDebugPrint(filename, patch, findings);
            analyzeTodo(filename, patch, findings);
            analyzeEmptyCatch(filename, patch, findings);
        }

        return findings;
    }

    private void analyzeDebugPrint(
        String filename,
        String patch,
        List<Finding> findings
    ) {

        if (DEBUG_PRINT_PATTERN.matcher(patch).find()) {

            findings.add(new Finding(
                AnalyzerType.CODE,
                FindingType.CODE_ISSUE,
                FindingSeverity.MEDIUM,
                RULE_DEBUG_PRINT,
                "Debug print detected",
                "System.out.println() was detected in the changed code.",
                filename,
                null
            ));
        }
    }

    private void analyzeTodo(
        String filename,
        String patch,
        List<Finding> findings
    ) {

        if (TODO_PATTERN.matcher(patch).find()) {

            findings.add(new Finding(
                AnalyzerType.CODE,
                FindingType.CODE_ISSUE,
                FindingSeverity.LOW,
                RULE_TODO,
                "TODO or FIXME detected",
                "TODO or FIXME marker was detected in the changed code.",
                filename,
                null
            ));
        }
    }

    private void analyzeEmptyCatch(
        String filename,
        String patch,
        List<Finding> findings
    ) {

        String addedLines = extractAddedLines(patch);

        if (EMPTY_CATCH_PATTERN.matcher(addedLines).find()) {

            findings.add(new Finding(
                AnalyzerType.CODE,
                FindingType.CODE_ISSUE,
                FindingSeverity.HIGH,
                RULE_EMPTY_CATCH,
                "Empty catch block detected",
                "An empty catch block was detected in the changed code.",
                filename,
                null
            ));
        }
    }

    private boolean isAnalyzableCodeFile(String filename) {

        return filename.endsWith(".java")
            || filename.endsWith(".js")
            || filename.endsWith(".ts")
            || filename.endsWith(".jsx")
            || filename.endsWith(".tsx")
            || filename.endsWith(".py")
            || filename.endsWith(".go")
            || filename.endsWith(".cs");
    }

    private String extractAddedLines(String patch) {

        return patch.lines()
            .filter(line -> line.startsWith("+") && !line.startsWith("+++"))
            .map(line -> line.substring(1))
            .reduce("", (result, line) -> result + line + "\n");
    }
}
