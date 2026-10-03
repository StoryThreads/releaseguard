import { useState } from 'react';
import type { FC } from 'react';
import { X, Play, Loader2, CheckCircle2, AlertTriangle, Cpu, GitPullRequest, Search } from 'lucide-react';
import { api, type GitHubPullRequestItem } from '../services/api';
import type { Project, Source, RiskLevel } from '../types';
import { RiskBadge } from './RiskBadge';

interface AnalysisProgressModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultProject?: Project;
  defaultSource?: Source;
  onAnalysisCompleted: (changeId: number) => void;
}

export const AnalysisProgressModal: FC<AnalysisProgressModalProps> = ({
  isOpen,
  onClose,
  defaultProject,
  defaultSource,
  onAnalysisCompleted,
}) => {
  const [urlInput, setUrlInput] = useState('');
  const [owner, setOwner] = useState(() => defaultSource?.repositoryOwner || defaultProject?.name.split('/')[0] || '');
  const [repo, setRepo] = useState(() => defaultSource?.repositoryName || defaultProject?.name.split('/')[1] || '');
  const [prNumber, setPrNumber] = useState<number | ''>('');

  // GitHub PR Discovery
  const [fetchingPrs, setFetchingPrs] = useState(false);
  const [fetchedPrs, setFetchedPrs] = useState<GitHubPullRequestItem[]>([]);
  const [fetchPrError, setFetchPrError] = useState<string | null>(null);

  // Execution states: 'IDLE' | 'QUEUED' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED'
  const [status, setStatus] = useState<'IDLE' | 'QUEUED' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED'>('IDLE');
  const [currentStep, setCurrentStep] = useState<string>('');
  const [correlationId, setCorrelationId] = useState<string>('');
  const [completedChangeId, setCompletedChangeId] = useState<number | null>(null);
  const [resultRisk, setResultRisk] = useState<RiskLevel | null>(null);
  const [resultScore, setResultScore] = useState<number>(0);
  const [resultFindingsCount, setResultFindingsCount] = useState<number>(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  // Helper to parse github url
  const handleUrlChange = (value: string) => {
    setUrlInput(value);
    const trimmed = value.trim();
    // Matches https://github.com/owner/repo/pull/123 or github.com/owner/repo/pull/123
    const prMatch = trimmed.match(/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/i);
    if (prMatch) {
      setOwner(prMatch[1]);
      setRepo(prMatch[2]);
      setPrNumber(Number(prMatch[3]));
      return;
    }
    // Matches owner/repo#123
    const shortMatch = trimmed.match(/^([^/\s]+)\/([^#\s]+)#(\d+)$/);
    if (shortMatch) {
      setOwner(shortMatch[1]);
      setRepo(shortMatch[2]);
      setPrNumber(Number(shortMatch[3]));
      return;
    }
    // Matches owner/repo
    const repoMatch = trimmed.match(/^([^/\s]+)\/([^/\s]+)$/);
    if (repoMatch) {
      setOwner(repoMatch[1]);
      setRepo(repoMatch[2]);
    }
  };

  const handleFetchRecentPrs = async () => {
    if (!owner.trim() || !repo.trim()) {
      setFetchPrError('Please enter owner and repository name first.');
      return;
    }
    setFetchingPrs(true);
    setFetchPrError(null);
    try {
      const prs = await api.getGitHubPullRequests(owner.trim(), repo.trim(), 'all', 8);
      setFetchedPrs(prs);
      if (prs.length === 0) {
        setFetchPrError(`No recent pull requests found for ${owner}/${repo}`);
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Could not fetch pull requests from GitHub';
      setFetchPrError(msg);
    } finally {
      setFetchingPrs(false);
    }
  };

  const startAnalysis = async () => {
    if (!owner.trim() || !repo.trim() || !prNumber) {
      setErrorMessage('Owner, repository name, and PR number are all required.');
      return;
    }

    setStatus('QUEUED');
    const corrId = 'corr-' + Math.random().toString(36).substring(2, 10);
    setCorrelationId(corrId);
    setCurrentStep('Dispatching analysis request to ReleaseGuard pipeline...');
    setErrorMessage(null);

    const step1 = setTimeout(() => {
      setStatus('IN_PROGRESS');
      setCurrentStep('Fetching PR diff & change snapshot from GitHub API...');
    }, 600);

    const step2 = setTimeout(() => {
      setCurrentStep('Running Static Analyzers (AST, Concurrency, Security rules)...');
    }, 1200);

    const step3 = setTimeout(() => {
      setCurrentStep('Extracting 28 normalized features & executing ML inference...');
    }, 1800);

    try {
      const res = await api.triggerAnalysis(
        defaultProject?.id,
        owner.trim(),
        repo.trim(),
        Number(prNumber)
      );

      clearTimeout(step1);
      clearTimeout(step2);
      clearTimeout(step3);

      setStatus('COMPLETED');
      setCurrentStep('Analysis persisted and finalized.');
      setCompletedChangeId(res.changeId);
      const riskInfo = res.riskAnalysis || res.prediction;
      setResultRisk((riskInfo?.riskLevel as RiskLevel) || 'LOW');
      setResultScore(riskInfo?.riskScore || 0);
      setResultFindingsCount(res.findings?.length || 0);
    } catch (err: unknown) {
      clearTimeout(step1);
      clearTimeout(step2);
      clearTimeout(step3);
      setStatus('FAILED');
      const msg = err instanceof Error ? err.message : 'Analysis failed. Please verify the repository and PR number.';
      setErrorMessage(msg);
    }
  };

  const handleReset = () => {
    setStatus('IDLE');
    setCurrentStep('');
    setErrorMessage(null);
    setCompletedChangeId(null);
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(8px)',
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px',
      }}
    >
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '560px',
          maxHeight: '90vh',
          overflowY: 'auto',
          padding: '28px',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px',
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '10px',
                backgroundColor: 'rgba(99, 102, 241, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#818cf8',
              }}
            >
              <Cpu size={22} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 600 }}>Analyze Pull Request</h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Target any GitHub repository for real-time defect risk prediction
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Input Form (shown when IDLE) */}
        {status === 'IDLE' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Quick URL paste */}
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                Quick Import: GitHub PR URL or Repo
              </label>
              <input
                type="text"
                placeholder="e.g. https://github.com/facebook/react/pull/31644 or owner/repo#123"
                value={urlInput}
                onChange={(e) => handleUrlChange(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  backgroundColor: 'var(--bg-input)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-main)',
                  fontSize: '0.88rem',
                  outline: 'none',
                }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                  Repository Owner *
                </label>
                <input
                  type="text"
                  placeholder="e.g. facebook, StoryThreads, pallets"
                  value={owner}
                  onChange={(e) => setOwner(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    borderRadius: '8px',
                    backgroundColor: 'var(--bg-input)',
                    border: '1px solid var(--border-subtle)',
                    color: 'var(--text-main)',
                    fontSize: '0.9rem',
                    outline: 'none',
                  }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                  Repository Name *
                </label>
                <input
                  type="text"
                  placeholder="e.g. react, releaseguard, flask"
                  value={repo}
                  onChange={(e) => setRepo(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    borderRadius: '8px',
                    backgroundColor: 'var(--bg-input)',
                    border: '1px solid var(--border-subtle)',
                    color: 'var(--text-main)',
                    fontSize: '0.9rem',
                    outline: 'none',
                  }}
                />
              </div>
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Pull Request # Number *
                </label>
                <button
                  type="button"
                  onClick={handleFetchRecentPrs}
                  disabled={fetchingPrs || !owner.trim() || !repo.trim()}
                  className="btn btn-secondary"
                  style={{ padding: '3px 8px', fontSize: '0.75rem', gap: '4px' }}
                >
                  {fetchingPrs ? <Loader2 size={12} className="spin" /> : <Search size={12} />}
                  Browse Live PRs
                </button>
              </div>
              <input
                type="number"
                placeholder="e.g. 1"
                value={prNumber}
                onChange={(e) => setPrNumber(e.target.value === '' ? '' : Number(e.target.value))}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  backgroundColor: 'var(--bg-input)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-main)',
                  fontSize: '0.9rem',
                  outline: 'none',
                }}
              />
            </div>

            {fetchPrError && (
              <div style={{ fontSize: '0.8rem', color: 'var(--risk-critical)' }}>
                {fetchPrError}
              </div>
            )}

            {/* List of fetched PRs if available */}
            {fetchedPrs.length > 0 && (
              <div
                style={{
                  backgroundColor: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '8px',
                  padding: '10px',
                  maxHeight: '160px',
                  overflowY: 'auto',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                }}
              >
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                  Select a live PR from {owner}/{repo}:
                </div>
                {fetchedPrs.map((pr: GitHubPullRequestItem) => (
                  <div
                    key={pr.number}
                    onClick={() => setPrNumber(pr.number)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '6px 8px',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '0.8rem',
                      backgroundColor: prNumber === pr.number ? 'rgba(99, 102, 241, 0.2)' : 'transparent',
                      border: prNumber === pr.number ? '1px solid rgba(99, 102, 241, 0.4)' : '1px solid transparent',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      <GitPullRequest size={14} color="#818cf8" />
                      <strong style={{ fontFamily: 'var(--font-mono)' }}>#{pr.number}</strong>
                      <span style={{ color: 'var(--text-main)', overflow: 'hidden', textOverflow: 'ellipsis' }}>{pr.title}</span>
                    </div>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                      @{pr.user?.login || 'user'}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {errorMessage && (
              <div style={{ color: 'var(--risk-critical)', fontSize: '0.85rem' }}>
                {errorMessage}
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '8px' }}>
              <button className="btn btn-secondary" onClick={onClose}>
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={startAnalysis}
                disabled={!owner.trim() || !repo.trim() || !prNumber}
              >
                <Play size={16} /> Run Analysis
              </button>
            </div>
          </div>
        )}

        {/* Progress Display */}
        {(status === 'QUEUED' || status === 'IN_PROGRESS') && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', padding: '12px 0' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <Loader2 size={24} className="spin" color="#818cf8" />
              <div>
                <div style={{ fontWeight: 600, fontSize: '1rem' }}>
                  {status === 'QUEUED' ? 'Analysis Queued...' : 'Analysis in Progress...'}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  Tracking ID: {correlationId}
                </div>
              </div>
            </div>

            <div
              style={{
                padding: '16px',
                borderRadius: '8px',
                backgroundColor: 'rgba(0, 0, 0, 0.3)',
                border: '1px solid var(--border-subtle)',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.85rem',
                color: '#a5b4fc',
              }}
            >
              {currentStep}
            </div>

            {/* Stepper */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.85rem' }}>
                <CheckCircle2 size={16} color="var(--risk-low)" />
                <span>Kafka request event dispatched</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.85rem' }}>
                <CheckCircle2 size={16} color="var(--risk-low)" />
                <span>GitHub pull request snapshot extracted</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.85rem' }}>
                <Loader2 size={16} className="spin" color="#818cf8" />
                <span>Running analyzers & ML model inference...</span>
              </div>
            </div>
          </div>
        )}

        {/* Completed State */}
        {status === 'COMPLETED' && (
          <div
            style={{
              padding: '20px',
              borderRadius: '12px',
              backgroundColor: 'rgba(16, 185, 129, 0.08)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--risk-low)' }}>
              <CheckCircle2 size={24} />
              <span style={{ fontWeight: 600, fontSize: '1.05rem' }}>Real Analysis Completed</span>
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '12px',
                padding: '16px',
                backgroundColor: 'var(--bg-canvas)',
                borderRadius: '8px',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Predicted Risk Level</span>
                <div style={{ marginTop: '4px' }}>
                  <RiskBadge level={resultRisk || 'LOW'} score={resultScore} />
                </div>
              </div>

              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Static Analyzer Findings</span>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, marginTop: '4px' }}>
                  {resultFindingsCount} Issues Found
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button className="btn btn-secondary" onClick={handleReset}>
                Analyze Another PR
              </button>
              <button
                className="btn btn-primary"
                onClick={() => {
                  if (completedChangeId) onAnalysisCompleted(completedChangeId);
                  onClose();
                }}
              >
                Inspect Results
              </button>
            </div>
          </div>
        )}

        {/* Failed State */}
        {status === 'FAILED' && (
          <div
            style={{
              padding: '20px',
              borderRadius: '12px',
              backgroundColor: 'rgba(239, 68, 68, 0.08)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--risk-critical)' }}>
              <AlertTriangle size={24} />
              <span style={{ fontWeight: 600, fontSize: '1.05rem' }}>Analysis Pipeline Failed</span>
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              {errorMessage || 'An error occurred during analysis execution.'}
            </p>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button className="btn btn-secondary" onClick={handleReset}>
                Try Again
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
