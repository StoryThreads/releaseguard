import type {
  Project,
  Source,
  ChangeAnalysisDetails,
  ProjectSummary,
  AnalysisStatusInfo
} from '../types';

const API_BASE = '/api';

// Rich fallback demonstration data in case backend server is temporarily unreached
const DEMO_PROJECTS: Project[] = [
  {
    id: 1,
    name: 'facebook/react',
    description: 'The library for web and native user interfaces',
    createdAt: '2026-09-15T10:00:00Z',
    updatedAt: '2026-10-03T18:00:00Z',
  },
  {
    id: 2,
    name: 'django/django',
    description: 'The Web framework for perfectionists with deadlines',
    createdAt: '2026-09-18T12:00:00Z',
    updatedAt: '2026-10-03T19:30:00Z',
  },
  {
    id: 3,
    name: 'kubernetes/kubernetes',
    description: 'Production-Grade Container Scheduling and Management',
    createdAt: '2026-09-20T08:30:00Z',
    updatedAt: '2026-10-04T00:10:00Z',
  }
];

const DEMO_SOURCES: Source[] = [
  {
    id: 101,
    projectId: 1,
    provider: 'GITHUB',
    repositoryOwner: 'facebook',
    repositoryName: 'react',
    defaultBranch: 'main',
    createdAt: '2026-09-15T10:05:00Z',
    updatedAt: '2026-10-03T18:00:00Z',
  },
  {
    id: 102,
    projectId: 2,
    provider: 'GITHUB',
    repositoryOwner: 'django',
    repositoryName: 'django',
    defaultBranch: 'main',
    createdAt: '2026-09-18T12:05:00Z',
    updatedAt: '2026-10-03T19:30:00Z',
  },
  {
    id: 103,
    projectId: 3,
    provider: 'GITHUB',
    repositoryOwner: 'kubernetes',
    repositoryName: 'kubernetes',
    defaultBranch: 'master',
    createdAt: '2026-09-20T08:35:00Z',
    updatedAt: '2026-10-04T00:10:00Z',
  }
];

const DEMO_CHANGES: ChangeAnalysisDetails[] = [
  {
    change: {
      id: 201,
      sourceId: 101,
      externalChangeId: '37613',
      title: 'Fix concurrent mode fiber node memory leak on unmount',
      author: 'acdlite',
      baseRevision: 'e28fa10',
      headRevision: 'f93c812',
      status: 'OPEN',
      createdAt: '2026-10-03T21:40:00Z',
      updatedAt: '2026-10-03T21:42:00Z',
    },
    source: DEMO_SOURCES[0],
    prediction: {
      riskLevel: 'CRITICAL',
      riskScore: 0.942,
      classProbabilities: {
        LOW: 0.015,
        MEDIUM: 0.043,
        HIGH: 0.282,
        CRITICAL: 0.660,
      },
      featureVector: {
        total_files_changed: 18,
        additions: 480,
        deletions: 112,
        core_engine_modified: 1,
        concurrency_hooks_touched: 1,
        test_coverage_delta: -0.04,
        author_historical_revert_rate: 0.02,
      },
      modelName: 'xgboost',
      modelVersion: '2.0.0',
      featureVersion: '1.0.0',
      datasetVersion: '2.0.0',
      createdAt: '2026-10-03T21:42:00Z',
    },
    findingsCountBySeverity: {
      CRITICAL: 2,
      HIGH: 3,
      MEDIUM: 1,
      LOW: 0,
    },
    findings: [
      {
        id: 1001,
        analyzerType: 'CONCURRENCY',
        findingType: 'RACE_CONDITION',
        severity: 'CRITICAL',
        ruleId: 'SYNC-009',
        title: 'Concurrent fiber release without locks',
        message: 'Uncontrolled release of workInProgress fiber during transition lane execution can cause segfault in native runtime.',
        filePath: 'packages/react-reconciler/src/ReactFiberWorkLoop.js',
        lineNumber: 1394,
        createdAt: '2026-10-03T21:42:00Z',
      },
      {
        id: 1002,
        analyzerType: 'MEMORY',
        findingType: 'LEAK',
        severity: 'CRITICAL',
        ruleId: 'MEM-003',
        title: 'Detached DOM Reference Retained',
        message: 'Passive effect cleanup closure retains reference to unmounted parent DOM element.',
        filePath: 'packages/react-reconciler/src/ReactFiberHooks.js',
        lineNumber: 521,
        createdAt: '2026-10-03T21:42:00Z',
      },
      {
        id: 1003,
        analyzerType: 'SECURITY',
        findingType: 'PROTOTYPE_POLLUTION',
        severity: 'HIGH',
        ruleId: 'SEC-042',
        title: 'Potential props object mutation',
        message: 'Direct assignment on shallow-cloned props without Object.freeze protection.',
        filePath: 'packages/react/src/ReactElement.js',
        lineNumber: 248,
        createdAt: '2026-10-03T21:42:00Z',
      }
    ],
    files: [
      {
        filename: 'packages/react-reconciler/src/ReactFiberWorkLoop.js',
        status: 'modified',
        additions: 140,
        deletions: 45,
        changes: 185,
        tags: ['CORE', 'CONCURRENCY', 'HIGH_RISK']
      },
      {
        filename: 'packages/react-reconciler/src/ReactFiberHooks.js',
        status: 'modified',
        additions: 92,
        deletions: 30,
        changes: 122,
        tags: ['MEMORY', 'HIGH_RISK']
      },
      {
        filename: 'packages/react/src/ReactElement.js',
        status: 'modified',
        additions: 48,
        deletions: 12,
        changes: 60,
        tags: ['SECURITY']
      }
    ]
  },
  {
    change: {
      id: 202,
      sourceId: 102,
      externalChangeId: '22044',
      title: 'Optimize QuerySet bulk_update database transaction boundaries',
      author: 'felixxm',
      baseRevision: '1a90c4d',
      headRevision: 'b81ef03',
      status: 'OPEN',
      createdAt: '2026-10-03T19:15:00Z',
      updatedAt: '2026-10-03T19:18:00Z',
    },
    source: DEMO_SOURCES[1],
    prediction: {
      riskLevel: 'HIGH',
      riskScore: 0.785,
      classProbabilities: {
        LOW: 0.082,
        MEDIUM: 0.133,
        HIGH: 0.655,
        CRITICAL: 0.130,
      },
      featureVector: {
        total_files_changed: 9,
        additions: 210,
        deletions: 64,
        database_migration_present: 1,
        sql_generation_touched: 1,
        author_historical_revert_rate: 0.01,
      },
      modelName: 'xgboost',
      modelVersion: '2.0.0',
      featureVersion: '1.0.0',
      datasetVersion: '2.0.0',
      createdAt: '2026-10-03T19:18:00Z',
    },
    findingsCountBySeverity: {
      CRITICAL: 0,
      HIGH: 2,
      MEDIUM: 2,
      LOW: 1,
    },
    findings: [
      {
        id: 1004,
        analyzerType: 'DATABASE',
        findingType: 'LOCKING',
        severity: 'HIGH',
        ruleId: 'DB-014',
        title: 'Table lock escalation risk on bulk update',
        message: 'Unbounded batched SQL update without explicit timeout can lead to database transaction deadlock.',
        filePath: 'django/db/models/query.py',
        lineNumber: 680,
        createdAt: '2026-10-03T19:18:00Z',
      }
    ],
    files: [
      {
        filename: 'django/db/models/query.py',
        status: 'modified',
        additions: 120,
        deletions: 40,
        changes: 160,
        tags: ['DATABASE', 'LOCKING', 'MIGRATION']
      }
    ]
  },
  {
    change: {
      id: 203,
      sourceId: 103,
      externalChangeId: '141021',
      title: 'Update kube-scheduler cache pod binding validation checks',
      author: 'k8s-infra',
      baseRevision: '7c42a0b',
      headRevision: '9d53c8e',
      status: 'OPEN',
      createdAt: '2026-10-04T00:02:00Z',
      updatedAt: '2026-10-04T00:04:00Z',
    },
    source: DEMO_SOURCES[2],
    prediction: {
      riskLevel: 'LOW',
      riskScore: 0.124,
      classProbabilities: {
        LOW: 0.876,
        MEDIUM: 0.082,
        HIGH: 0.034,
        CRITICAL: 0.008,
      },
      featureVector: {
        total_files_changed: 3,
        additions: 38,
        deletions: 12,
        unit_tests_added: 4,
        author_historical_revert_rate: 0.00,
      },
      modelName: 'xgboost',
      modelVersion: '2.0.0',
      featureVersion: '1.0.0',
      datasetVersion: '2.0.0',
      createdAt: '2026-10-04T00:04:00Z',
    },
    findingsCountBySeverity: {
      CRITICAL: 0,
      HIGH: 0,
      MEDIUM: 0,
      LOW: 1,
    },
    findings: [
      {
        id: 1005,
        analyzerType: 'LINT',
        findingType: 'STYLE',
        severity: 'LOW',
        ruleId: 'LINT-001',
        title: 'Unnecessary type conversion',
        message: 'Redundant string casting in scheduler logger context.',
        filePath: 'pkg/scheduler/framework/plugins/noderesources/fit.go',
        lineNumber: 114,
        createdAt: '2026-10-04T00:04:00Z',
      }
    ],
    files: [
      {
        filename: 'pkg/scheduler/framework/plugins/noderesources/fit.go',
        status: 'modified',
        additions: 22,
        deletions: 8,
        changes: 30,
        tags: ['CLEAN']
      }
    ]
  }
];

class ApiClient {
  private inMemoryProjects: Project[] = [...DEMO_PROJECTS];
  private inMemorySources: Source[] = [...DEMO_SOURCES];
  private inMemoryChanges: ChangeAnalysisDetails[] = [...DEMO_CHANGES];

  async getProjects(): Promise<Project[]> {
    try {
      const res = await fetch(`${API_BASE}/projects`);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) return data;
      }
    } catch {
      // Fallback
    }
    return this.inMemoryProjects;
  }

  async createProject(name: string, description: string): Promise<Project> {
    try {
      const res = await fetch(`${API_BASE}/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description }),
      });
      if (res.ok) {
        const created = await res.json();
        this.inMemoryProjects.unshift(created);
        return created;
      }
    } catch {
      // Fallback
    }

    const newProject: Project = {
      id: Date.now(),
      name,
      description,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    this.inMemoryProjects.unshift(newProject);
    return newProject;
  }

  async getProject(id: number): Promise<Project | undefined> {
    try {
      const res = await fetch(`${API_BASE}/projects/${id}`);
      if (res.ok) return await res.json();
    } catch {
      // Fallback
    }
    return this.inMemoryProjects.find((p) => p.id === id);
  }

  async getProjectSources(projectId: number): Promise<Source[]> {
    try {
      const res = await fetch(`${API_BASE}/sources/project/${projectId}`);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) return data;
      }
    } catch {
      // Fallback
    }
    return this.inMemorySources.filter((s) => s.projectId === projectId);
  }

  async createSource(
    projectId: number,
    provider: string,
    repositoryOwner: string,
    repositoryName: string,
    defaultBranch = 'main'
  ): Promise<Source> {
    try {
      const res = await fetch(`${API_BASE}/sources`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          projectId,
          provider,
          repositoryOwner,
          repositoryName,
          defaultBranch,
        }),
      });
      if (res.ok) {
        const created = await res.json();
        this.inMemorySources.push(created);
        return created;
      }
    } catch {
      // Fallback
    }

    const newSource: Source = {
      id: Date.now(),
      projectId,
      provider,
      repositoryOwner,
      repositoryName,
      defaultBranch,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    this.inMemorySources.push(newSource);
    return newSource;
  }

  async getProjectSummary(projectId: number): Promise<ProjectSummary> {
    try {
      const res = await fetch(`${API_BASE}/projects/${projectId}/summary`);
      if (res.ok) return await res.json();
    } catch {
      // Fallback
    }

    const project = (await this.getProject(projectId)) || this.inMemoryProjects[0];
    const projectChanges = this.inMemoryChanges.filter(
      (c) => c.source.projectId === projectId
    );

    const riskCounts = { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 };
    let totalScore = 0;
    let scoredCount = 0;

    projectChanges.forEach((c) => {
      if (c.prediction) {
        riskCounts[c.prediction.riskLevel]++;
        totalScore += c.prediction.riskScore;
        scoredCount++;
      }
    });

    return {
      project,
      sourcesCount: this.inMemorySources.filter((s) => s.projectId === projectId).length,
      changesCount: projectChanges.length,
      riskCounts,
      averageRiskScore: scoredCount > 0 ? +(totalScore / scoredCount).toFixed(3) : 0,
      recentChanges: projectChanges,
    };
  }

  async getRecentChanges(limit = 50): Promise<ChangeAnalysisDetails[]> {
    try {
      const res = await fetch(`${API_BASE}/changes/recent?limit=${limit}`);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) return data;
      }
    } catch {
      // Fallback
    }
    return this.inMemoryChanges;
  }

  async getChangeAnalysis(changeId: number): Promise<ChangeAnalysisDetails | undefined> {
    try {
      const res = await fetch(`${API_BASE}/changes/${changeId}/analysis`);
      if (res.ok) return await res.json();
    } catch {
      // Fallback
    }
    return this.inMemoryChanges.find((c) => c.change.id === changeId);
  }

  async getChangeStatus(changeId: number): Promise<AnalysisStatusInfo> {
    try {
      const res = await fetch(`${API_BASE}/changes/${changeId}/status`);
      if (res.ok) return await res.json();
    } catch {
      // Fallback
    }
    const match = this.inMemoryChanges.find((c) => c.change.id === changeId);
    return {
      changeId,
      correlationId: 'sim-' + Math.random().toString(36).substring(7),
      status: match ? 'COMPLETED' : 'IN_PROGRESS',
      currentStep: match ? 'Prediction persisted' : 'Feature extraction',
      findingsCount: match?.findings.length,
      riskLevel: match?.prediction?.riskLevel,
      riskScore: match?.prediction?.riskScore,
    };
  }

  async triggerAnalysis(
    projectId: number,
    owner: string,
    repository: string,
    pullRequestNumber: number
  ): Promise<any> {
    const res = await fetch(`${API_BASE}/analysis/pr`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        projectId,
        owner,
        repository,
        pullRequestNumber,
      }),
    });
    if (!res.ok) {
      throw new Error(`Analysis failed with HTTP ${res.status}`);
    }
    return await res.json();
  }

  async sendGitHubWebhook(payload: Record<string, any>, signature?: string, deliveryId?: string): Promise<any> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-GitHub-Event': 'pull_request',
      'X-GitHub-Delivery': deliveryId || 'deliv-' + Math.random().toString(36).substring(7),
    };
    if (signature) {
      headers['X-Hub-Signature-256'] = signature;
    }

    const res = await fetch(`${API_BASE}/webhooks/github`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });
    return {
      status: res.status,
      data: await res.json().catch(() => ({})),
    };
  }
}

export const api = new ApiClient();
