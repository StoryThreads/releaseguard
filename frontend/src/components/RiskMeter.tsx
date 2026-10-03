import type { FC } from 'react';
import type { RiskLevel } from '../types';

interface RiskMeterProps {
  score: number;
  level: RiskLevel | string;
  size?: number;
  modelName?: string;
  modelVersion?: string;
}

export const RiskMeter: FC<RiskMeterProps> = ({
  score,
  level,
  size = 140,
  modelName = 'xgboost',
  modelVersion = '2.0.0',
}) => {
  const percentage = Math.min(Math.max(Math.round(score * 100), 0), 100);
  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  const getColor = () => {
    switch ((level || '').toUpperCase()) {
      case 'CRITICAL':
        return '#f43f5e';
      case 'HIGH':
        return '#f97316';
      case 'MEDIUM':
        return '#eab308';
      case 'LOW':
      default:
        return '#10b981';
    }
  };

  const color = getColor();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
      <div style={{ position: 'relative', width: size, height: size }}>
        <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="rgba(255, 255, 255, 0.08)"
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          {/* Active progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={color}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            style={{
              transition: 'stroke-dashoffset 0.8s cubic-bezier(0.16, 1, 0.3, 1), stroke 0.3s ease',
              filter: `drop-shadow(0 0 8px ${color})`,
            }}
          />
        </svg>

        {/* Center score readout */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <span style={{ fontSize: size * 0.24, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
            {percentage}%
          </span>
          <span style={{ fontSize: size * 0.09, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Risk Score
          </span>
        </div>
      </div>

      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textAlign: 'center', fontFamily: 'var(--font-mono)' }}>
        {modelName} v{modelVersion}
      </div>
    </div>
  );
};
