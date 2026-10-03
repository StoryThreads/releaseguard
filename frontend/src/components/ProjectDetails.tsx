import { useState, useEffect } from 'react';
import type { FC } from 'react';
import type { Project, Source, ProjectSummary } from '../types';
import { api } from '../services/api';
import { ArrowLeft, GitBranch, GitPullRequest, History, ExternalLink } from 'lucide-react';
import { RiskBadge } from './RiskBadge';
import { RiskMeter } from './RiskMeter';

interface ProjectDetailsProps {
  projectId: number;
  onBack: () => void;
  onSelectChange: (changeId: number) => void;
  onOpenSourceModal: (project: Project) => void;
  onOpenAnalysisModal: (project: Project, source?: Source) => void;
}

export const ProjectDetails: FC<ProjectDetailsProps> = ({
  projectId,
  onBack,
  onSelectChange,
  onOpenSourceModal,
  onOpenAnalysisModal,
}) => {
  const [summary, setSummary] = useState<ProjectSummary | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'history' | 'sources'>('history');

  const loadData = async () => {
    setLoading(true);
    try {
      const [sum, srcList] = await Promise.all([
        api.getProjectSummary(projectId),
        api.getProjectSources(projectId),
      ]);
      setSummary(sum || null);
      setSources(srcList);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [projectId]);

  if (loading || !summary) {
    return (
      <div style={{ textAlign: 'center', padding: '64px', color: 'var(--text-muted)' }}>
        Loading project details...
      </div>
    );
  }

  const { project, riskCounts, averageRiskScore, recentChanges } = summary;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Top breadcrumb & back */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button
          onClick={onBack}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: 'transparent',
            border: 'none',
            color: 'var(--text-muted)',
            fontSize: '0.85rem',
            cursor: 'pointer',
          }}
        >
          <ArrowLeft size={16} /> Back to Projects
        </button>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            className="btn btn-secondary"
            onClick={() => onOpenSourceModal(project)}
          >
            <GitBranch size={16} /> Add Repository
          </button>
          <button
            className="btn btn-primary"
            onClick={() => onOpenAnalysisModal(project, sources[0])}
          >
            <GitPullRequest size={16} /> Analyze PR
          </button>
        </div>
      </div>

      {/* Project Overview Card */}
      <div
        className="glass-panel"
        style={{
          padding: '28px',
          display: 'grid',
          gridTemplateColumns: '2fr 1fr',
          gap: '24px',
          alignItems: 'center',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 700 }}>{project.name}</h1>
            <span className="badge badge-subtle">{sources.length} Connected Repos</span>
          </div>
          <p style={{ color: 'var(--text-muted)', marginTop: '8px', fontSize: '0.95rem' }}>
            {project.description || 'No description provided.'}
          </p>

          <div style={{ display: 'flex', gap: '16px', marginTop: '20px', flexWrap: 'wrap' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
              Created: <span style={{ color: 'var(--text-muted)' }}>{new Date(project.createdAt).toLocaleDateString()}</span>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
              Last Analyzed: <span style={{ color: 'var(--text-muted)' }}>{new Date(project.updatedAt).toLocaleDateString()}</span>
            </div>
          </div>
        </div>

        {/* Project risk summary gauge */}
        <div style={{ display: 'flex', justifyContent: 'center', borderLeft: '1px solid var(--border-subtle)', paddingLeft: '24px' }}>
          <RiskMeter
            score={averageRiskScore}
            level={
              averageRiskScore >= 0.75
                ? 'CRITICAL'
                : averageRiskScore >= 0.5
                ? 'HIGH'
                : averageRiskScore >= 0.25
                ? 'MEDIUM'
                : 'LOW'
            }
            size={120}
          />
        </div>
      </div>

      {/* Risk Metrics Quick Row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '16px',
        }}
      >
        <div
          className="glass-panel"
          style={{
            padding: '16px 20px',
            borderLeft: '4px solid var(--risk-critical)',
          }}
        >
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>CRITICAL RISK PRs</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--risk-critical)', fontFamily: 'var(--font-mono)' }}>
            {riskCounts.CRITICAL || 0}
          </div>
        </div>

        <div
          className="glass-panel"
          style={{
            padding: '16px 20px',
            borderLeft: '4px solid var(--risk-high)',
          }}
        >
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>HIGH RISK PRs</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--risk-high)', fontFamily: 'var(--font-mono)' }}>
            {riskCounts.HIGH || 0}
          </div>
        </div>

        <div
          className="glass-panel"
          style={{
            padding: '16px 20px',
            borderLeft: '4px solid var(--risk-medium)',
          }}
        >
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>MEDIUM RISK PRs</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--risk-medium)', fontFamily: 'var(--font-mono)' }}>
            {riskCounts.MEDIUM || 0}
          </div>
        </div>

        <div
          className="glass-panel"
          style={{
            padding: '16px 20px',
            borderLeft: '4px solid var(--risk-low)',
          }}
        >
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>LOW RISK PRs</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--risk-low)', fontFamily: 'var(--font-mono)' }}>
            {riskCounts.LOW || 0}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border-subtle)', gap: '16px' }}>
        <button
          onClick={() => setActiveTab('history')}
          style={{
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'history' ? '2px solid #818cf8' : '2px solid transparent',
            color: activeTab === 'history' ? '#818cf8' : 'var(--text-muted)',
            fontWeight: 600,
            padding: '10px 16px',
            cursor: 'pointer',
            fontSize: '0.9rem',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <History size={16} /> Analysis History ({recentChanges.length})
        </button>

        <button
          onClick={() => setActiveTab('sources')}
          style={{
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'sources' ? '2px solid #818cf8' : '2px solid transparent',
            color: activeTab === 'sources' ? '#818cf8' : 'var(--text-muted)',
            fontWeight: 600,
            padding: '10px 16px',
            cursor: 'pointer',
            fontSize: '0.9rem',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <GitBranch size={16} /> Connected Repositories ({sources.length})
        </button>
      </div>

      {/* Tab 1: Analysis History */}
      {activeTab === 'history' && (
        <div className="glass-panel" style={{ overflow: 'hidden' }}>
          {recentChanges.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)' }}>
              No PR analyses recorded yet for this project.
            </div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ backgroundColor: 'rgba(255, 255, 255, 0.02)', borderBottom: '1px solid var(--border-subtle)' }}>
                  <th style={{ padding: '14px 20px', color: 'var(--text-dim)', fontWeight: 600 }}>PR / TITLE</th>
                  <th style={{ padding: '14px 20px', color: 'var(--text-dim)', fontWeight: 600 }}>AUTHOR</th>
                  <th style={{ padding: '14px 20px', color: 'var(--text-dim)', fontWeight: 600 }}>RISK LEVEL</th>
                  <th style={{ padding: '14px 20px', color: 'var(--text-dim)', fontWeight: 600 }}>SCORE</th>
                  <th style={{ padding: '14px 20px', color: 'var(--text-dim)', fontWeight: 600 }}>FINDINGS</th>
                  <th style={{ padding: '14px 20px', color: 'var(--text-dim)', fontWeight: 600 }}>DATE</th>
                  <th style={{ padding: '14px 20px', color: 'var(--text-dim)', fontWeight: 600 }}>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {recentChanges.map((item) => (
                  <tr
                    key={item.change.id}
                    onClick={() => onSelectChange(item.change.id)}
                    style={{
                      borderBottom: '1px solid var(--border-subtle)',
                      cursor: 'pointer',
                      transition: 'background-color 0.15s',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.03)')}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                  >
                    <td style={{ padding: '16px 20px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontFamily: 'var(--font-mono)', color: '#818cf8', fontWeight: 600 }}>
                          #{item.change.externalChangeId}
                        </span>
                        <span style={{ fontWeight: 500, color: 'var(--text-main)' }}>{item.change.title}</span>
                      </div>
                    </td>
                    <td style={{ padding: '16px 20px', color: 'var(--text-muted)' }}>
                      @{item.change.author}
                    </td>
                    <td style={{ padding: '16px 20px' }}>
                      <RiskBadge level={item.prediction?.riskLevel || 'LOW'} />
                    </td>
                    <td style={{ padding: '16px 20px', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                      {item.prediction ? `${(item.prediction.riskScore * 100).toFixed(0)}%` : '—'}
                    </td>
                    <td style={{ padding: '16px 20px' }}>
                      <span className="badge badge-subtle">{item.findings.length} findings</span>
                    </td>
                    <td style={{ padding: '16px 20px', color: 'var(--text-dim)' }}>
                      {new Date(item.change.createdAt).toLocaleDateString()}
                    </td>
                    <td style={{ padding: '16px 20px' }}>
                      <span style={{ color: '#818cf8', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        Details <ExternalLink size={12} />
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Tab 2: Connected Sources */}
      {activeTab === 'sources' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
          {sources.map((src) => (
            <div
              key={src.id}
              className="glass-panel"
              style={{
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <GitBranch size={18} color="#818cf8" />
                  <span style={{ fontWeight: 600, fontSize: '1rem' }}>
                    {src.repositoryOwner}/{src.repositoryName}
                  </span>
                </div>
                <span className="badge badge-subtle">{src.provider}</span>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Default Branch: <code>{src.defaultBranch}</code>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                Connected on {new Date(src.createdAt).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
