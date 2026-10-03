export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type FindingSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export type AnalysisStatus = 'QUEUED' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';

export interface Project {
  id: number;
  name: string;
  description: string;
  createdAt: string;
  updatedAt: string;
}

export interface Source {
  id: number;
  projectId: number;
  provider: string;
  repositoryOwner: string;
  repositoryName: string;
  defaultBranch: string;
  createdAt: string;
  updatedAt: string;
}

export interface Change {
  id: number;
  sourceId: number;
  externalChangeId: string;
  title: string;
  author: string;
  baseRevision: string;
  headRevision: string;
  status: string;
  createdAt: string;
  updatedAt: string;
}

export interface Finding {
  id: number;
  analyzerType: string;
  findingType: string;
  severity: FindingSeverity;
  ruleId: string;
  title: string;
  message: string;
  filePath?: string;
  lineNumber?: number;
  createdAt: string;
}

export interface DetailedPrediction {
  riskLevel: RiskLevel;
  riskScore: number;
  classProbabilities: {
    LOW?: number;
    MEDIUM?: number;
    HIGH?: number;
    CRITICAL?: number;
    [key: string]: number | undefined;
  };
  featureVector: Record<string, number | string | boolean>;
  modelName: string;
  modelVersion: string;
  featureVersion: string;
  datasetVersion: string;
  createdAt: string;
}

export interface ChangedFile {
  filename: string;
  status: 'added' | 'modified' | 'removed' | 'renamed';
  additions: number;
  deletions: number;
  changes: number;
  patch?: string;
  tags?: string[];
}

export interface ChangeAnalysisDetails {
  change: Change;
  source: Source;
  prediction?: DetailedPrediction;
  findings: Finding[];
  findingsCountBySeverity: Record<string, number>;
  files?: ChangedFile[];
}

export interface ProjectSummary {
  project: Project;
  sourcesCount: number;
  changesCount: number;
  riskCounts: {
    LOW: number;
    MEDIUM: number;
    HIGH: number;
    CRITICAL: number;
  };
  averageRiskScore: number;
  recentChanges: ChangeAnalysisDetails[];
}

export interface AnalysisStatusInfo {
  changeId?: number;
  correlationId: string;
  status: AnalysisStatus;
  currentStep?: string;
  message?: string;
  findingsCount?: number;
  riskLevel?: RiskLevel;
  riskScore?: number;
}
