import { useState, useEffect } from 'react';
import type { FC } from 'react';
import type { ChangeAnalysisDetails, Project } from '../types';
import { api } from '../services/api';
import { Search, ArrowRight, Play, GitPullRequest } from 'lucide-react';
import { RiskBadge } from './RiskBadge';

interface PullRequestListProps {
  onSelectChange: (changeId: number) => void;
  selectedProjectId?: number;
  onOpenAnalysisModal?: () => void;
}

export const PullRequestList: FC<PullRequestListProps> = ({
  onSelectChange,
  selectedProjectId,
  onOpenAnalysisModal,
}) => {
  const [changes, setChanges] = useState<ChangeAnalysisDetails[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterRisk, setFilterRisk] = useState<string>('ALL');
  const [filterProject, setFilterProject] = useState<string>(
    selectedProjectId ? String(selectedProjectId) : 'ALL'
  );

  const loadData = async () => {
    setLoading(true);
    try {
      const [allChanges, allProjects] = await Promise.all([
        api.getRecentChanges(100),
        api.getProjects(),
      ]);
      setChanges(allChanges);
      setProjects(allProjects);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedProjectId]);

  const filteredChanges = changes.filter((item) => {
    if (filterRisk !== 'ALL' && item.prediction?.riskLevel !== filterRisk) return false;
    if (filterProject !== 'ALL' && String(item.source.projectId) !== filterProject) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        item.change.title.toLowerCase().includes(q) ||
        item.change.externalChangeId.includes(q) ||
        item.change.author.toLowerCase().includes(q) ||
        item.source.repositoryName.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700, marginBottom: '6px' }}>
          Pull Requests
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          Monitored pull requests with pre-release defect risk prediction and static analysis findings.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div
        className="glass-panel"
        style={{
          padding: '16px 20px',
          display: 'flex',
          gap: '16px',
          alignItems: 'center',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
          {/* Search */}
          <div style={{ position: 'relative', width: '280px' }}>
            <Search
              size={15}
              style={{
                position: 'absolute',
                left: '12px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--text-dim)',
              }}
            />
            <input
              type="text"
              placeholder="Search PR title, author, #..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px 8px 36px',
                borderRadius: '8px',
                backgroundColor: 'var(--bg-input)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-main)',
                fontSize: '0.85rem',
                outline: 'none',
              }}
            />
          </div>

          {/* Project Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Project:</span>
            <select
              value={filterProject}
              onChange={(e) => setFilterProject(e.target.value)}
              style={{
                padding: '6px 10px',
                borderRadius: '6px',
                backgroundColor: 'var(--bg-input)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-main)',
                fontSize: '0.8rem',
                outline: 'none',
              }}
            >
              <option value="ALL">All Projects</option>
              {projects.map((p) => (
                <option key={p.id} value={String(p.id)}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          {/* Risk Level Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Risk:</span>
            <select
              value={filterRisk}
              onChange={(e) => setFilterRisk(e.target.value)}
              style={{
                padding: '6px 10px',
                borderRadius: '6px',
                backgroundColor: 'var(--bg-input)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-main)',
                fontSize: '0.8rem',
                outline: 'none',
              }}
            >
              <option value="ALL">All Risk Levels</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>
        </div>

        <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
          Showing <strong>{filteredChanges.length}</strong> of {changes.length} PRs
        </div>
      </div>

      {/* PR Table */}
      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)' }}>
            Loading pull requests...
          </div>
        ) : filteredChanges.length === 0 ? (
          <div
            style={{
              textAlign: 'center',
              padding: '48px 24px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '14px',
            }}
          >
            <GitPullRequest size={42} color="#818cf8" style={{ opacity: 0.6 }} />
            <div>
              <div style={{ fontWeight: 600, fontSize: '1.05rem', color: 'var(--text-main)', marginBottom: '4px' }}>
                {changes.length === 0 ? 'No Pull Requests Analyzed Yet' : 'No Pull Requests Match Filters'}
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', maxWidth: '400px' }}>
                {changes.length === 0
                  ? 'Analyze any repository pull request directly to compute risk scores and detect defects.'
                  : 'Try adjusting your search query, project filter, or risk level filter.'}
              </div>
            </div>
            {changes.length === 0 && onOpenAnalysisModal && (
              <button className="btn btn-primary" onClick={onOpenAnalysisModal} style={{ marginTop: '6px' }}>
                <Play size={14} /> Analyze Pull Request
              </button>
            )}
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ backgroundColor: 'rgba(255, 255, 255, 0.02)', borderBottom: '1px solid var(--border-subtle)' }}>
                <th style={{ padding: '14px 20px', color: 'var(--text-dim)', fontWeight: 600 }}>PR / TITLE</th>
                <th style={{ padding: '14px 20px', color: 'var(--text-dim)', fontWeight: 600 }}>REPOSITORY</th>
                <th style={{ padding: '14px 20px', color: 'var(--text-dim)', fontWeight: 600 }}>AUTHOR</th>
                <th style={{ padding: '14px 20px', color: 'var(--text-dim)', fontWeight: 600 }}>RISK PREDICTION</th>
                <th style={{ padding: '14px 20px', color: 'var(--text-dim)', fontWeight: 600 }}>SCORE</th>
                <th style={{ padding: '14px 20px', color: 'var(--text-dim)', fontWeight: 600 }}>FINDINGS</th>
                <th style={{ padding: '14px 20px', color: 'var(--text-dim)', fontWeight: 600 }}>UPDATED</th>
                <th style={{ padding: '14px 20px', color: 'var(--text-dim)', fontWeight: 600 }}>ACTION</th>
              </tr>
            </thead>
            <tbody>
              {filteredChanges.map((item) => (
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
                    {item.source.repositoryOwner}/{item.source.repositoryName}
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
                    <span className="badge badge-subtle">
                      {item.findings.length} finding{item.findings.length !== 1 ? 's' : ''}
                    </span>
                  </td>
                  <td style={{ padding: '16px 20px', color: 'var(--text-dim)' }}>
                    {new Date(item.change.updatedAt).toLocaleDateString()}
                  </td>
                  <td style={{ padding: '16px 20px' }}>
                    <div style={{ color: '#818cf8', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <span>Inspect</span>
                      <ArrowRight size={13} />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
