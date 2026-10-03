import type {
  Project,
  Source,
  ChangeAnalysisDetails,
  ProjectSummary,
  AnalysisStatusInfo
} from '../types';

const API_BASE = '/api';

export interface GitHubPullRequestItem {
  number: number;
  title: string;
  state: string;
  created_at?: string;
  updated_at?: string;
  html_url?: string;
  user?: { login: string };
  head?: { ref: string; sha: string };
  base?: { ref: string; sha: string };
}

export interface AnalysisTriggerResponse {
  changeId: number;
  snapshot: Record<string, unknown>;
  findings: Array<Record<string, unknown>>;
  riskAnalysis?: {
    riskLevel?: string;
    riskScore?: number;
    modelName?: string;
    modelVersion?: string;
    [key: string]: unknown;
  };
  prediction?: {
    riskLevel?: string;
    riskScore?: number;
    modelName?: string;
    modelVersion?: string;
    [key: string]: unknown;
  };
}

export interface WebhookSendResponse {
  status: number;
  data: Record<string, unknown>;
}

class ApiClient {
  async getProjects(): Promise<Project[]> {
    try {
      const res = await fetch(`${API_BASE}/projects`);
      if (res.ok) {
        return await res.json();
      }
    } catch (e) {
      console.error('Failed to fetch projects from backend:', e);
    }
    return [];
  }

  async createProject(name: string, description?: string): Promise<Project> {
    const res = await fetch(`${API_BASE}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description }),
    });
    if (!res.ok) {
      const msg = await res.text().catch(() => '');
      throw new Error(`Failed to create project: ${msg || res.statusText}`);
    }
    return await res.json();
  }

  async getProject(id: number): Promise<Project | undefined> {
    try {
      const res = await fetch(`${API_BASE}/projects/${id}`);
      if (res.ok) return await res.json();
    } catch (e) {
      console.error(`Failed to fetch project ${id}:`, e);
    }
    return undefined;
  }

  async getProjectSources(projectId: number): Promise<Source[]> {
    try {
      const res = await fetch(`${API_BASE}/sources/project/${projectId}`);
      if (res.ok) return await res.json();
    } catch (e) {
      console.error(`Failed to fetch sources for project ${projectId}:`, e);
    }
    return [];
  }

  async createSource(
    projectId: number,
    provider: string,
    repositoryOwner: string,
    repositoryName: string,
    defaultBranch = 'main'
  ): Promise<Source> {
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
    if (!res.ok) {
      const msg = await res.text().catch(() => '');
      throw new Error(`Failed to create source: ${msg || res.statusText}`);
    }
    return await res.json();
  }

  async getProjectSummary(projectId: number): Promise<ProjectSummary | undefined> {
    try {
      const res = await fetch(`${API_BASE}/projects/${projectId}/summary`);
      if (res.ok) return await res.json();
    } catch (e) {
      console.error(`Failed to fetch summary for project ${projectId}:`, e);
    }
    return undefined;
  }

  async getRecentChanges(limit = 50): Promise<ChangeAnalysisDetails[]> {
    try {
      const res = await fetch(`${API_BASE}/changes/recent?limit=${limit}`);
      if (res.ok) {
        const data = await res.json();
        return Array.isArray(data) ? data : [];
      }
    } catch (e) {
      console.error('Failed to fetch recent changes:', e);
    }
    return [];
  }

  async getProjectChanges(projectId: number): Promise<ChangeAnalysisDetails[]> {
    try {
      const res = await fetch(`${API_BASE}/projects/${projectId}/changes`);
      if (res.ok) {
        const data = await res.json();
        return Array.isArray(data) ? data : [];
      }
    } catch (e) {
      console.error(`Failed to fetch changes for project ${projectId}:`, e);
    }
    return [];
  }

  async getChangeAnalysis(changeId: number): Promise<ChangeAnalysisDetails | undefined> {
    try {
      const res = await fetch(`${API_BASE}/changes/${changeId}/analysis`);
      if (res.ok) return await res.json();
    } catch (e) {
      console.error(`Failed to fetch analysis for change ${changeId}:`, e);
    }
    return undefined;
  }

  async getChangeStatus(changeId: number): Promise<AnalysisStatusInfo | undefined> {
    try {
      const res = await fetch(`${API_BASE}/changes/${changeId}/status`);
      if (res.ok) return await res.json();
    } catch (e) {
      console.error(`Failed to fetch status for change ${changeId}:`, e);
    }
    return undefined;
  }

  async getGitHubPullRequests(
    owner: string,
    repo: string,
    state = 'open',
    limit = 10
  ): Promise<GitHubPullRequestItem[]> {
    const res = await fetch(
      `${API_BASE}/analysis/github/pulls?owner=${encodeURIComponent(owner)}&repo=${encodeURIComponent(repo)}&state=${encodeURIComponent(state)}&limit=${limit}`
    );
    if (!res.ok) {
      const msg = await res.text().catch(() => '');
      throw new Error(`Failed to fetch PRs from GitHub: ${msg || res.statusText}`);
    }
    return await res.json();
  }

  async triggerAnalysis(
    projectId: number | undefined,
    owner: string,
    repository: string,
    pullRequestNumber: number
  ): Promise<AnalysisTriggerResponse> {
    const payload: Record<string, string | number> = {
      owner: owner.trim(),
      repository: repository.trim(),
      pullRequestNumber: Number(pullRequestNumber),
    };
    if (projectId && projectId > 0) {
      payload.projectId = projectId;
    }

    const res = await fetch(`${API_BASE}/analysis/pr`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const msg = await res.text().catch(() => '');
      throw new Error(`Analysis failed (${res.status}): ${msg || res.statusText}`);
    }
    return await res.json();
  }

  async sendGitHubWebhook(
    payload: Record<string, unknown>,
    signature?: string,
    deliveryId?: string
  ): Promise<WebhookSendResponse> {
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
