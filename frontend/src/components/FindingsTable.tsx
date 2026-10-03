import { useState, Fragment } from 'react';
import type { FC } from 'react';
import type { Finding, FindingSeverity } from '../types';
import { Search, FileCode, ChevronDown, ChevronRight } from 'lucide-react';

interface FindingsTableProps {
  findings: Finding[];
}

export const FindingsTable: FC<FindingsTableProps> = ({ findings }) => {
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');
  const [filterAnalyzer, setFilterAnalyzer] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedRow, setExpandedRow] = useState<number | null>(null);

  // Extract unique analyzer types
  const analyzerTypes = Array.from(new Set(findings.map((f) => f.analyzerType)));

  // Filter findings
  const filtered = findings.filter((f) => {
    if (filterSeverity !== 'ALL' && f.severity !== filterSeverity) return false;
    if (filterAnalyzer !== 'ALL' && f.analyzerType !== filterAnalyzer) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        f.title.toLowerCase().includes(q) ||
        f.message.toLowerCase().includes(q) ||
        f.ruleId.toLowerCase().includes(q) ||
        (f.filePath && f.filePath.toLowerCase().includes(q))
      );
    }
    return true;
  });

  const getSeverityBadgeClass = (severity: FindingSeverity) => {
    switch (severity) {
      case 'CRITICAL':
        return 'badge-critical';
      case 'HIGH':
        return 'badge-high';
      case 'MEDIUM':
        return 'badge-medium';
      case 'LOW':
      default:
        return 'badge-low';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Filter and Search Bar */}
      <div
        style={{
          display: 'flex',
          gap: '12px',
          alignItems: 'center',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
          {/* Search Input */}
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
              placeholder="Search findings, rules, files..."
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

          {/* Severity Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Severity:</span>
            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
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
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>

          {/* Analyzer Filter */}
          {analyzerTypes.length > 1 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Analyzer:</span>
              <select
                value={filterAnalyzer}
                onChange={(e) => setFilterAnalyzer(e.target.value)}
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
                <option value="ALL">All Analyzers</option>
                {analyzerTypes.map((a) => (
                  <option key={a} value={a}>
                    {a}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
          Showing <strong>{filtered.length}</strong> of {findings.length} findings
        </div>
      </div>

      {/* Findings Table */}
      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        {filtered.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            No findings match the selected criteria.
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ backgroundColor: 'rgba(255, 255, 255, 0.02)', borderBottom: '1px solid var(--border-subtle)' }}>
                <th style={{ width: '40px', padding: '12px 16px' }}></th>
                <th style={{ padding: '12px 16px', color: 'var(--text-dim)', fontWeight: 600 }}>SEVERITY</th>
                <th style={{ padding: '12px 16px', color: 'var(--text-dim)', fontWeight: 600 }}>RULE / ID</th>
                <th style={{ padding: '12px 16px', color: 'var(--text-dim)', fontWeight: 600 }}>TITLE & DESCRIPTION</th>
                <th style={{ padding: '12px 16px', color: 'var(--text-dim)', fontWeight: 600 }}>ANALYZER SOURCE</th>
                <th style={{ padding: '12px 16px', color: 'var(--text-dim)', fontWeight: 600 }}>FILE & LINE</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((f) => {
                const isExpanded = expandedRow === f.id;
                return (
                  <Fragment key={f.id}>
                    <tr
                      onClick={() => setExpandedRow(isExpanded ? null : f.id)}
                      style={{
                        borderBottom: '1px solid var(--border-subtle)',
                        cursor: 'pointer',
                        transition: 'background-color 0.15s',
                        backgroundColor: isExpanded ? 'rgba(99, 102, 241, 0.06)' : 'transparent',
                      }}
                      onMouseEnter={(e) => {
                        if (!isExpanded) e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.02)';
                      }}
                      onMouseLeave={(e) => {
                        if (!isExpanded) e.currentTarget.style.backgroundColor = 'transparent';
                      }}
                    >
                      <td style={{ padding: '14px 16px', color: 'var(--text-dim)' }}>
                        {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                      </td>
                      <td style={{ padding: '14px 16px' }}>
                        <span className={`badge ${getSeverityBadgeClass(f.severity)}`}>
                          {f.severity}
                        </span>
                      </td>
                      <td style={{ padding: '14px 16px', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#818cf8' }}>
                        {f.ruleId}
                      </td>
                      <td style={{ padding: '14px 16px' }}>
                        <div style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: '2px' }}>
                          {f.title}
                        </div>
                        <div
                          style={{
                            fontSize: '0.78rem',
                            color: 'var(--text-muted)',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            maxWidth: '420px',
                          }}
                        >
                          {f.message}
                        </div>
                      </td>
                      <td style={{ padding: '14px 16px' }}>
                        <span className="badge badge-subtle">
                          {f.analyzerType}
                        </span>
                      </td>
                      <td style={{ padding: '14px 16px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                        {f.filePath ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <FileCode size={14} color="#818cf8" />
                            <span>
                              {f.filePath.split('/').pop()}
                              {f.lineNumber ? `:${f.lineNumber}` : ''}
                            </span>
                          </div>
                        ) : (
                          '—'
                        )}
                      </td>
                    </tr>

                    {/* Expandable details row */}
                    {isExpanded && (
                      <tr style={{ backgroundColor: 'rgba(99, 102, 241, 0.04)', borderBottom: '1px solid var(--border-subtle)' }}>
                        <td colSpan={6} style={{ padding: '18px 24px' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                            <div>
                              <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600 }}>
                                Full Explanation
                              </span>
                              <p style={{ marginTop: '4px', fontSize: '0.9rem', color: 'var(--text-main)', lineHeight: 1.5 }}>
                                {f.message}
                              </p>
                            </div>

                            {f.filePath && (
                              <div>
                                <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600 }}>
                                  Location Reference
                                </span>
                                <div
                                  style={{
                                    marginTop: '4px',
                                    padding: '8px 12px',
                                    borderRadius: '6px',
                                    backgroundColor: 'var(--bg-canvas)',
                                    fontFamily: 'var(--font-mono)',
                                    fontSize: '0.8rem',
                                    color: '#818cf8',
                                    display: 'inline-block',
                                  }}
                                >
                                  {f.filePath}{f.lineNumber ? ` (Line ${f.lineNumber})` : ''}
                                </div>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
