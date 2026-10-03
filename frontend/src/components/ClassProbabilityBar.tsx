import type { FC } from 'react';

interface ClassProbabilityBarProps {
  probabilities?: {
    LOW?: number;
    MEDIUM?: number;
    HIGH?: number;
    CRITICAL?: number;
    [key: string]: number | undefined;
  };
}

export const ClassProbabilityBar: FC<ClassProbabilityBarProps> = ({ probabilities = {} }) => {
  const pLow = probabilities.LOW || 0;
  const pMed = probabilities.MEDIUM || 0;
  const pHigh = probabilities.HIGH || 0;
  const pCrit = probabilities.CRITICAL || 0;

  const total = pLow + pMed + pHigh + pCrit;
  const normLow = total > 0 ? (pLow / total) * 100 : 25;
  const normMed = total > 0 ? (pMed / total) * 100 : 25;
  const normHigh = total > 0 ? (pHigh / total) * 100 : 25;
  const normCrit = total > 0 ? (pCrit / total) * 100 : 25;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
        <span>Class Probabilities</span>
        <span style={{ fontFamily: 'var(--font-mono)' }}>p(class | features)</span>
      </div>

      {/* Stacked bar */}
      <div
        style={{
          display: 'flex',
          height: '10px',
          borderRadius: '5px',
          overflow: 'hidden',
          backgroundColor: 'rgba(255, 255, 255, 0.05)',
          gap: '2px',
        }}
      >
        {normLow > 0 && (
          <div
            title={`LOW: ${(pLow * 100).toFixed(1)}%`}
            style={{ width: `${normLow}%`, backgroundColor: 'var(--risk-low)', transition: 'width 0.5s' }}
          />
        )}
        {normMed > 0 && (
          <div
            title={`MEDIUM: ${(pMed * 100).toFixed(1)}%`}
            style={{ width: `${normMed}%`, backgroundColor: 'var(--risk-medium)', transition: 'width 0.5s' }}
          />
        )}
        {normHigh > 0 && (
          <div
            title={`HIGH: ${(pHigh * 100).toFixed(1)}%`}
            style={{ width: `${normHigh}%`, backgroundColor: 'var(--risk-high)', transition: 'width 0.5s' }}
          />
        )}
        {normCrit > 0 && (
          <div
            title={`CRITICAL: ${(pCrit * 100).toFixed(1)}%`}
            style={{ width: `${normCrit}%`, backgroundColor: 'var(--risk-critical)', transition: 'width 0.5s' }}
          />
        )}
      </div>

      {/* Grid labels */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '8px',
          fontSize: '0.75rem',
          fontFamily: 'var(--font-mono)',
        }}
      >
        <div style={{ color: 'var(--risk-low)' }}>
          LOW: {(pLow * 100).toFixed(1)}%
        </div>
        <div style={{ color: 'var(--risk-medium)' }}>
          MED: {(pMed * 100).toFixed(1)}%
        </div>
        <div style={{ color: 'var(--risk-high)' }}>
          HIGH: {(pHigh * 100).toFixed(1)}%
        </div>
        <div style={{ color: 'var(--risk-critical)' }}>
          CRIT: {(pCrit * 100).toFixed(1)}%
        </div>
      </div>
    </div>
  );
};
