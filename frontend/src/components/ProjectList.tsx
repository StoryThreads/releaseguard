import { useState, useEffect } from 'react';
import type { FC } from 'react';
import type { Project, ProjectSummary } from '../types';
import { api } from '../services/api';
import { Plus, FolderGit2, GitPullRequest, ArrowRight, Activity, GitBranch } from 'lucide-react';
import { RiskBadge } from './RiskBadge';

interface ProjectListProps {
  onSelectProject: (projectId: number) => void;
  onOpenSourceModal: (project: Project) => void;
  onBrowsePullRequests: (projectId?: number) => void;
  onOpenAnalysisModal?: () => void;
}

export const ProjectList: FC<ProjectListProps> = ({
  onSelectProject,
  onOpenSourceModal,
  onBrowsePullRequests,
  onOpenAnalysisModal,
}) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [summaries, setSummaries] = useState<Record<number, ProjectSummary>>({});
  const [loading, setLoading] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');
  const [creating, setCreating] = useState(false);

  const loadProjects = async () => {
    setLoading(true);
    try {
      const data = await api.getProjects();
      setProjects(data);

      // Load summaries in parallel
      const summaryMap: Record<number, ProjectSummary> = {};
      for (const p of data) {
        try {
          const sum = await api.getProjectSummary(p.id);
          if (sum) {
            summaryMap[p.id] = sum;
          }
        } catch {
          // Ignore
        }
      }
      setSummaries(summaryMap);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;

    setCreating(true);
    try {
      const created = await api.createProject(newProjectName.trim(), newProjectDesc.trim());
      setIsCreateModalOpen(false);
      setNewProjectName('');
      setNewProjectDesc('');
      await loadProjects();
      onSelectProject(created.id);
    } catch (err) {
      console.error(err);
    } finally {
      setCreating(false);
    }
  };

  // Compute aggregate stats across projects
  const totalPrs = Object.values(summaries).reduce((acc, s) => acc + s.changesCount, 0);
  const highRiskPrs = Object.values(summaries).reduce(
    (acc, s) => acc + (s.riskCounts.HIGH || 0) + (s.riskCounts.CRITICAL || 0),
    0
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      {/* Hero / Header stats banner */}
      <div
        className="glass-panel"
        style={{
          padding: '28px 32px',
          background: 'linear-gradient(135deg, rgba(24, 32, 54, 0.95), rgba(14, 19, 32, 0.9))',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '24px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#818cf8', fontSize: '0.85rem', fontWeight: 600 }}>
            <Activity size={16} /> RELEASEGUARD INTELLIGENCE
          </div>
          <h1 style={{ fontSize: '1.85rem', fontWeight: 700, margin: '6px 0 4px' }}>
            Projects & Repositories
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '600px' }}>
            Real-time pre-release defect prediction, continuous risk scoring, and automated static analyzer findings.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <div
            style={{
              padding: '12px 20px',
              backgroundColor: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '10px',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '1.4rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
              {projects.length}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Monitored Projects
            </div>
          </div>

          <div
            style={{
              padding: '12px 20px',
              backgroundColor: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '10px',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '1.4rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
              {totalPrs}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Analyzed PRs
            </div>
          </div>

          <div
            style={{
              padding: '12px 20px',
              backgroundColor: 'var(--risk-critical-bg)',
              border: '1px solid var(--risk-critical-border)',
              borderRadius: '10px',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--risk-critical)', fontFamily: 'var(--font-mono)' }}>
              {highRiskPrs}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--risk-critical)', textTransform: 'uppercase' }}>
              High/Critical PRs
            </div>
          </div>

          <button className="btn btn-primary" onClick={() => setIsCreateModalOpen(true)}>
            <Plus size={16} /> New Project
          </button>
        </div>
      </div>

      {/* Projects Grid */}
      <div>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '16px' }}>
          Registered Projects ({projects.length})
        </h2>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)' }}>
            Loading ReleaseGuard projects...
          </div>
        ) : projects.length === 0 ? (
          <div
            className="glass-panel"
            style={{
              padding: '48px 24px',
              textAlign: 'center',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '16px',
            }}
          >
            <FolderGit2 size={48} color="#818cf8" style={{ opacity: 0.6 }} />
            <div>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '6px' }}>
                No Projects Monitored Yet
              </h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '460px' }}>
                Analyze any GitHub repository pull request directly, or register a new project workspace.
              </p>
            </div>
            <div style={{ display: 'flex', gap: '12px', marginTop: '8px' }}>
              {onOpenAnalysisModal && (
                <button className="btn btn-primary" onClick={onOpenAnalysisModal}>
                  <GitPullRequest size={16} /> Analyze Any GitHub Repo
                </button>
              )}
              <button className="btn btn-secondary" onClick={() => setIsCreateModalOpen(true)}>
                <Plus size={16} /> Create Project
              </button>
            </div>
          </div>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))',
              gap: '20px',
            }}
          >
            {projects.map((p) => {
              const summary = summaries[p.id];
              const riskCounts = summary?.riskCounts || { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 };
              const avgScore = summary?.averageRiskScore || 0;

              return (
                <div
                  key={p.id}
                  className="glass-panel"
                  style={{
                    padding: '24px',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    gap: '20px',
                    transition: 'all 0.2s',
                    cursor: 'pointer',
                  }}
                  onClick={() => onSelectProject(p.id)}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = 'rgba(99, 102, 241, 0.4)';
                    e.currentTarget.style.transform = 'translateY(-2px)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = 'var(--border-subtle)';
                    e.currentTarget.style.transform = 'none';
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
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
                          <FolderGit2 size={20} />
                        </div>
                        <div>
                          <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>{p.name}</h3>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                            Updated {new Date(p.updatedAt).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                      <span className="badge badge-subtle">
                        {summary?.sourcesCount || 1} repo{summary?.sourcesCount !== 1 ? 's' : ''}
                      </span>
                    </div>

                    <p
                      style={{
                        fontSize: '0.85rem',
                        color: 'var(--text-muted)',
                        marginTop: '12px',
                        lineHeight: 1.4,
                        minHeight: '38px',
                      }}
                    >
                      {p.description || 'No description provided.'}
                    </p>
                  </div>

                  {/* Project-level risk distribution pills */}
                  <div
                    style={{
                      padding: '12px 14px',
                      backgroundColor: 'rgba(255, 255, 255, 0.02)',
                      borderRadius: '8px',
                      border: '1px solid var(--border-subtle)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '8px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      <span>Risk Profile</span>
                      <span>Avg Score: <strong>{(avgScore * 100).toFixed(0)}%</strong></span>
                    </div>
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                      <RiskBadge level="CRITICAL" score={undefined} />
                      <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--risk-critical)', marginRight: '8px' }}>
                        {riskCounts.CRITICAL}
                      </span>

                      <RiskBadge level="HIGH" score={undefined} />
                      <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--risk-high)', marginRight: '8px' }}>
                        {riskCounts.HIGH}
                      </span>

                      <RiskBadge level="MEDIUM" score={undefined} />
                      <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--risk-medium)', marginRight: '8px' }}>
                        {riskCounts.MEDIUM}
                      </span>

                      <RiskBadge level="LOW" score={undefined} />
                      <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--risk-low)' }}>
                        {riskCounts.LOW}
                      </span>
                    </div>
                  </div>

                  {/* Card footer actions */}
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      paddingTop: '8px',
                      borderTop: '1px solid var(--border-subtle)',
                    }}
                  >
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        className="btn btn-secondary"
                        style={{ padding: '6px 12px', fontSize: '0.8rem' }}
                        onClick={(e) => {
                          e.stopPropagation();
                          onOpenSourceModal(p);
                        }}
                      >
                        <GitBranch size={14} /> Add Source
                      </button>

                      <button
                        className="btn btn-secondary"
                        style={{ padding: '6px 12px', fontSize: '0.8rem' }}
                        onClick={(e) => {
                          e.stopPropagation();
                          onBrowsePullRequests(p.id);
                        }}
                      >
                        <GitPullRequest size={14} /> PRs
                      </button>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#818cf8', fontSize: '0.85rem', fontWeight: 500 }}>
                      <span>View Details</span>
                      <ArrowRight size={14} />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Create Project Modal */}
      {isCreateModalOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
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
              maxWidth: '480px',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px',
            }}
          >
            <h3 style={{ fontSize: '1.2rem', fontWeight: 600 }}>Create New Project</h3>
            <form onSubmit={handleCreateProject} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                  Project Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. facebook/react"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  required
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
                  Description
                </label>
                <textarea
                  placeholder="Brief description of project repository or architecture..."
                  value={newProjectDesc}
                  onChange={(e) => setNewProjectDesc(e.target.value)}
                  rows={3}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    borderRadius: '8px',
                    backgroundColor: 'var(--bg-input)',
                    border: '1px solid var(--border-subtle)',
                    color: 'var(--text-main)',
                    fontSize: '0.9rem',
                    outline: 'none',
                    resize: 'vertical',
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setIsCreateModalOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={creating}>
                  {creating ? 'Creating...' : 'Create Project'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
