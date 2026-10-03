import { useState, useEffect } from 'react';
import type { FC } from 'react';
import type { ChangeAnalysisDetails } from '../types';
import { api } from '../services/api';
import {
  ArrowLeft,
  ExternalLink,
  FileCode,
  Cpu,
  ShieldCheck,
  Clock,
  User,
  Plus,
  Minus,
  Sparkles
} from 'lucide-react';
import { RiskBadge } from './RiskBadge';
import { RiskMeter } from './RiskMeter';
import { ClassProbabilityBar } from './ClassProbabilityBar';
import { FindingsTable } from './FindingsTable';

interface PullRequestDetailsProps {
  changeId: number;
  onBack: () => void;
}

export const PullRequestDetails: FC<PullRequestDetailsProps> = ({
  changeId,
  onBack,
}) => {
  const [details, setDetails] = useState<ChangeAnalysisDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'findings' | 'files' | 'features'>('findings');

  useEffect(() => {
    loadDetails();
  }, [changeId]);

  const loadDetails = async () => {
    setLoading(true);
    try {
      const data = await api.getChangeAnalysis(changeId);
      if (data) setDetails(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !details) {
    return (
      <div style={{ textAlign: 'center', padding: '64px', color: 'var(--text-muted)' }}>
        Loading pull request analysis details...
      </div>
    );
  }

  const { change, source, prediction, findings, files = [] } = details;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Back button */}
      <div>
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
          <ArrowLeft size={16} /> Back to Pull Requests
        </button>
      </div>

      {/* PR Header Banner */}
      <div
        className="glass-panel"
        style={{
          padding: '24px 28px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1.25rem', fontWeight: 700, color: '#818cf8' }}>
                #{change.externalChangeId}
              </span>
              <span className="badge badge-subtle">{change.status}</span>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                {source.repositoryOwner}/{source.repositoryName}
              </span>
            </div>

            <h1 style={{ fontSize: '1.6rem', fontWeight: 700, lineHeight: 1.3 }}>
              {change.title}
            </h1>
          </div>

          <a
            href={`https://github.com/${source.repositoryOwner}/${source.repositoryName}/pull/${change.externalChangeId}`}
            target="_blank"
            rel="noreferrer"
            className="btn btn-secondary"
            style={{ fontSize: '0.85rem' }}
          >
            <ExternalLink size={14} /> View on GitHub
          </a>
        </div>

        {/* PR Metadata bar */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '24px',
            flexWrap: 'wrap',
            paddingTop: '16px',
            borderTop: '1px solid var(--border-subtle)',
            fontSize: '0.85rem',
            color: 'var(--text-muted)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <User size={15} /> Author: <strong style={{ color: 'var(--text-main)' }}>@{change.author}</strong>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontFamily: 'var(--font-mono)' }}>
            Branch: <span style={{ color: '#818cf8' }}>{change.baseRevision}</span> ← <span style={{ color: '#818cf8' }}>{change.headRevision}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Clock size={15} /> Created: {new Date(change.createdAt).toLocaleString()}
          </div>
        </div>
      </div>

      {/* Risk Visualization Banner (V0.9.5) */}
      {prediction && (
        <div
          className="glass-panel"
          style={{
            padding: '24px 28px',
            display: 'grid',
            gridTemplateColumns: '160px 1fr 220px',
            gap: '28px',
            alignItems: 'center',
            background: 'linear-gradient(135deg, rgba(24, 32, 54, 0.95), rgba(14, 19, 32, 0.9))',
          }}
        >
          {/* Circular Risk Score */}
          <RiskMeter
            score={prediction.riskScore}
            level={prediction.riskLevel}
            size={130}
            modelName={prediction.modelName}
            modelVersion={prediction.modelVersion}
          />

          {/* Middle: Level Badge & Class Probabilities */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <RiskBadge level={prediction.riskLevel} score={prediction.riskScore} />
              <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                {prediction.riskLevel === 'CRITICAL' && 'Immediate review required. High probability of rollback or post-merge defect.'}
                {prediction.riskLevel === 'HIGH' && 'Elevated defect risk. Thorough architectural & security review advised.'}
                {prediction.riskLevel === 'MEDIUM' && 'Moderate defect probability. Verify edge cases and regressions.'}
                {prediction.riskLevel === 'LOW' && 'Low risk. Standard review procedure applies.'}
              </span>
            </div>

            <ClassProbabilityBar probabilities={prediction.classProbabilities} />
          </div>

          {/* Model / Version Metadata Card */}
          <div
            style={{
              padding: '16px',
              backgroundColor: 'rgba(255, 255, 255, 0.03)',
              borderRadius: '10px',
              border: '1px solid var(--border-subtle)',
              fontSize: '0.78rem',
              color: 'var(--text-muted)',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#818cf8', fontWeight: 600 }}>
              <Sparkles size={14} /> ML Model Intelligence
            </div>
            <div>Architecture: <strong>{prediction.modelName.toUpperCase()}</strong></div>
            <div>Model Version: <code>v{prediction.modelVersion}</code></div>
            <div>Feature Schema: <code>v{prediction.featureVersion} (28 features)</code></div>
            <div>Dataset Trained: <code>v{prediction.datasetVersion}</code></div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border-subtle)', gap: '16px' }}>
        <button
          onClick={() => setActiveTab('findings')}
          style={{
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'findings' ? '2px solid #818cf8' : '2px solid transparent',
            color: activeTab === 'findings' ? '#818cf8' : 'var(--text-muted)',
            fontWeight: 600,
            padding: '10px 16px',
            cursor: 'pointer',
            fontSize: '0.9rem',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <ShieldCheck size={16} /> Static Findings ({findings.length})
        </button>

        <button
          onClick={() => setActiveTab('files')}
          style={{
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'files' ? '2px solid #818cf8' : '2px solid transparent',
            color: activeTab === 'files' ? '#818cf8' : 'var(--text-muted)',
            fontWeight: 600,
            padding: '10px 16px',
            cursor: 'pointer',
            fontSize: '0.9rem',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <FileCode size={16} /> Changed Files & Diff Summary ({files.length || 3})
        </button>

        <button
          onClick={() => setActiveTab('features')}
          style={{
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'features' ? '2px solid #818cf8' : '2px solid transparent',
            color: activeTab === 'features' ? '#818cf8' : 'var(--text-muted)',
            fontWeight: 600,
            padding: '10px 16px',
            cursor: 'pointer',
            fontSize: '0.9rem',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <Cpu size={16} /> 28 ML Normalized Features
        </button>
      </div>

      {/* Tab 1: Findings Table */}
      {activeTab === 'findings' && <FindingsTable findings={findings} />}

      {/* Tab 2: Changed Files */}
      {activeTab === 'files' && (
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Diff & Changed Files</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {files.map((file, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  backgroundColor: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <FileCode size={16} color="#818cf8" />
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.88rem' }}>{file.filename}</span>
                  {file.tags?.map((t, tidx) => (
                    <span
                      key={tidx}
                      className="badge"
                      style={{
                        backgroundColor: t.includes('RISK') ? 'var(--risk-critical-bg)' : 'rgba(255, 255, 255, 0.05)',
                        color: t.includes('RISK') ? 'var(--risk-critical)' : 'var(--text-muted)',
                      }}
                    >
                      {t}
                    </span>
                  ))}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>
                  <span style={{ color: 'var(--risk-low)', display: 'flex', alignItems: 'center', gap: '2px' }}>
                    <Plus size={13} /> {file.additions}
                  </span>
                  <span style={{ color: 'var(--risk-critical)', display: 'flex', alignItems: 'center', gap: '2px' }}>
                    <Minus size={13} /> {file.deletions}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 3: Feature Vector */}
      {activeTab === 'features' && (
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Normalized Feature Vector</h3>
            <span className="badge badge-subtle">ReleaseGuard Feature Schema v1.0.0</span>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
              gap: '12px',
            }}
          >
            {prediction?.featureVector &&
              Object.entries(prediction.featureVector).map(([key, val]) => (
                <div
                  key={key}
                  style={{
                    padding: '12px 14px',
                    borderRadius: '8px',
                    backgroundColor: 'rgba(255, 255, 255, 0.02)',
                    border: '1px solid var(--border-subtle)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{key}</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#818cf8', fontSize: '0.85rem' }}>
                    {typeof val === 'number' ? val.toFixed(3) : String(val)}
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
};
