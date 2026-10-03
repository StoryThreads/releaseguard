import type { FC } from 'react';
import type { RiskLevel } from '../types';
import { AlertTriangle, ShieldAlert, AlertCircle, ShieldCheck } from 'lucide-react';

interface RiskBadgeProps {
  level: RiskLevel | string;
  score?: number;
  showIcon?: boolean;
}

export const RiskBadge: FC<RiskBadgeProps> = ({ level, score, showIcon = true }) => {
  const normalizedLevel = (level || 'LOW').toUpperCase();

  const getIcon = () => {
    switch (normalizedLevel) {
      case 'CRITICAL':
        return <AlertTriangle size={13} strokeWidth={2.5} />;
      case 'HIGH':
        return <ShieldAlert size={13} strokeWidth={2.5} />;
      case 'MEDIUM':
        return <AlertCircle size={13} strokeWidth={2.5} />;
      case 'LOW':
      default:
        return <ShieldCheck size={13} strokeWidth={2.5} />;
    }
  };

  const badgeClass = `badge badge-${normalizedLevel.toLowerCase()}`;

  return (
    <span className={badgeClass} title={`Risk Level: ${normalizedLevel}${score !== undefined ? ` (${(score * 100).toFixed(1)}%)` : ''}`}>
      {showIcon && getIcon()}
      <span>{normalizedLevel}</span>
      {score !== undefined && (
        <span style={{ opacity: 0.8, marginLeft: '3px' }}>
          {(score * 100).toFixed(0)}%
        </span>
      )}
    </span>
  );
};
