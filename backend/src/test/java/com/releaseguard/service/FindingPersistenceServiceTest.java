package com.releaseguard.service;

import com.releaseguard.analyzer.*;
import com.releaseguard.entity.Change;
import com.releaseguard.entity.FindingEntity;
import com.releaseguard.repository.FindingRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Captor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.anyList;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class FindingPersistenceServiceTest {

    @Mock
    private FindingRepository findingRepository;

    @Captor
    private ArgumentCaptor<List<FindingEntity>> captor;

    @InjectMocks
    private FindingPersistenceService service;

    @Test
    void shouldPersistFindings() {

        Change change = new Change();

        Finding finding = new Finding(
            AnalyzerType.CODE,
            FindingType.CODE_ISSUE,
            FindingSeverity.MEDIUM,
            "CODE-001",
            "Empty catch block",
            "An empty catch block was detected.",
            "src/main/java/Test.java",
            25
        );

        FindingEntity savedEntity = new FindingEntity();

        when(findingRepository.saveAll(anyList()))
            .thenReturn(List.of(savedEntity));

        List<FindingEntity> result =
            service.replaceFindings(
                change,
                List.of(finding)
            );

        assertEquals(1, result.size());

        verify(findingRepository).saveAll(captor.capture());

        List<FindingEntity> entities =
            captor.getValue();

        assertEquals(1, entities.size());

        FindingEntity entity = entities.get(0);

        assertEquals(change, entity.getChange());
        assertEquals("CODE", entity.getAnalyzerType());
        assertEquals("CODE_ISSUE", entity.getFindingType());
        assertEquals("MEDIUM", entity.getSeverity());
        assertEquals("CODE-001", entity.getRuleId());
        assertEquals("Empty catch block", entity.getTitle());
        assertEquals(
            "An empty catch block was detected.",
            entity.getMessage()
        );
        assertEquals(
            "src/main/java/Test.java",
            entity.getFilePath()
        );
        assertEquals(25, entity.getLineNumber());
    }

    @Test
    void shouldPersistMultipleFindings() {

        Change change = new Change();

        Finding first = new Finding(
            AnalyzerType.CODE,
            FindingType.CODE_ISSUE,
            FindingSeverity.MEDIUM,
            "CODE-001",
            "Issue 1",
            "Message 1",
            "Test.java",
            10
        );

        Finding second = new Finding(
            AnalyzerType.API,
            FindingType.API_ISSUE,
            FindingSeverity.MEDIUM,
            "API-001",
            "Issue 2",
            "Message 2",
            "Controller.java",
            20
        );

        when(findingRepository.saveAll(anyList()))
            .thenAnswer(invocation -> invocation.getArgument(0));

        List<FindingEntity> result =
            service.replaceFindings(
                change,
                List.of(first, second)
            );

        assertEquals(2, result.size());

        verify(findingRepository).saveAll(anyList());
    }

    @Test
    void shouldReturnEmptyWhenFindingsAreEmpty() {

        Change change = new Change();

        List<FindingEntity> result =
            service.replaceFindings(
                change,
                List.of()
            );

        assertTrue(result.isEmpty());

        verify(findingRepository, never()).saveAll(anyList());
    }

    @Test
    void shouldReturnEmptyWhenFindingsAreNull() {

        Change change = new Change();

        List<FindingEntity> result =
            service.replaceFindings(
                change,
                null
            );

        assertTrue(result.isEmpty());

        verify(findingRepository, never()).saveAll(anyList());
    }

    @Test
    void shouldReturnEmptyWhenChangeIsNull() {

        Finding finding = new Finding(
            AnalyzerType.CODE,
            FindingType.CODE_ISSUE,
            FindingSeverity.MEDIUM,
            "CODE-001",
            "Issue",
            "Message",
            "Test.java",
            10
        );

        List<FindingEntity> result =
            service.replaceFindings(
                null,
                List.of(finding)
            );

        assertTrue(result.isEmpty());

        verify(findingRepository, never()).saveAll(anyList());
    }

    @Test
    void shouldRetrieveFindingsForChange() {

        FindingEntity first = new FindingEntity();
        FindingEntity second = new FindingEntity();

        when(
            findingRepository.findByChangeIdOrderByIdAsc(10L)
        ).thenReturn(
            List.of(first, second)
        );

        List<FindingEntity> result =
            service.getFindings(10L);

        assertEquals(2, result.size());

        verify(
            findingRepository
        ).findByChangeIdOrderByIdAsc(10L);
    }

    @Test
    void shouldReturnEmptyWhenChangeIdIsNull() {

        List<FindingEntity> result =
            service.getFindings(null);

        assertTrue(result.isEmpty());

        verify(
            findingRepository,
            never()
        ).findByChangeIdOrderByIdAsc(any());
    }

    @Test
    void shouldCountFindings() {

        when(
            findingRepository.countByChangeId(10L)
        ).thenReturn(5L);

        long count =
            service.countFindings(10L);

        assertEquals(5L, count);

        verify(
            findingRepository
        ).countByChangeId(10L);
    }
}
