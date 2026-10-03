import React from 'react';
import { Shield, GitPullRequest, FolderGit2, Zap, Play } from 'lucide-react';

interface NavbarProps {
  currentTab: 'projects' | 'pull-requests' | 'webhooks';
  onSelectTab: (tab: 'projects' | 'pull-requests' | 'webhooks') => void;
  onOpenAnalysisModal: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  onSelectTab,
  onOpenAnalysisModal,
}) => {
  return (
    <header
      style={{
        height: 'var(--navbar-height)',
        borderBottom: '1px solid var(--border-subtle)',
        background: 'rgba(9, 13, 22, 0.85)',
        backdropFilter: 'blur(16px)',
        position: 'sticky',
        top: 0,
        zIndex: 50,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 32px',
      }}
    >
      {/* Brand */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          cursor: 'pointer',
        }}
        onClick={() => onSelectTab('projects')}
      >
        <div
          style={{
            background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
            width: '36px',
            height: '36px',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 16px rgba(99, 102, 241, 0.4)',
          }}
        >
          <Shield size={20} color="#fff" strokeWidth={2.5} />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontWeight: 800, fontSize: '1.15rem', letterSpacing: '-0.02em' }}>
              ReleaseGuard
            </span>
            <span
              style={{
                fontSize: '0.65rem',
                fontFamily: 'var(--font-mono)',
                backgroundColor: 'rgba(99, 102, 241, 0.15)',
                color: '#818cf8',
                border: '1px solid rgba(99, 102, 241, 0.3)',
                padding: '2px 6px',
                borderRadius: '4px',
                fontWeight: 600,
              }}
            >
              v2.0.0
            </span>
          </div>
          <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            Pre-Release Risk Intelligence & Automation
          </p>
        </div>
      </div>

      {/* Nav Links */}
      <nav style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <button
          onClick={() => onSelectTab('projects')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 16px',
            borderRadius: '8px',
            border: 'none',
            fontSize: '0.875rem',
            fontWeight: 500,
            cursor: 'pointer',
            backgroundColor: currentTab === 'projects' ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
            color: currentTab === 'projects' ? '#818cf8' : 'var(--text-muted)',
            transition: 'all 0.2s',
          }}
        >
          <FolderGit2 size={16} />
          <span>Projects</span>
        </button>

        <button
          onClick={() => onSelectTab('pull-requests')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 16px',
            borderRadius: '8px',
            border: 'none',
            fontSize: '0.875rem',
            fontWeight: 500,
            cursor: 'pointer',
            backgroundColor: currentTab === 'pull-requests' ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
            color: currentTab === 'pull-requests' ? '#818cf8' : 'var(--text-muted)',
            transition: 'all 0.2s',
          }}
        >
          <GitPullRequest size={16} />
          <span>Pull Requests</span>
        </button>

        <button
          onClick={() => onSelectTab('webhooks')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 16px',
            borderRadius: '8px',
            border: 'none',
            fontSize: '0.875rem',
            fontWeight: 500,
            cursor: 'pointer',
            backgroundColor: currentTab === 'webhooks' ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
            color: currentTab === 'webhooks' ? '#818cf8' : 'var(--text-muted)',
            transition: 'all 0.2s',
          }}
        >
          <Zap size={16} />
          <span>Webhook Simulator</span>
        </button>
      </nav>

      {/* Action Button */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <button
          className="btn btn-primary"
          onClick={onOpenAnalysisModal}
          style={{ padding: '8px 16px' }}
        >
          <Play size={14} fill="#fff" />
          <span>Run Analysis</span>
        </button>
      </div>
    </header>
  );
};
