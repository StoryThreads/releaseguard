import { useState } from 'react';
import type { FC } from 'react';
import { Zap, Send, CheckCircle2, AlertTriangle, RefreshCw } from 'lucide-react';
import { api } from '../services/api';

export const WebhookSimulator: FC = () => {
  const [owner, setOwner] = useState('facebook');
  const [repo, setRepo] = useState('react');
  const [prNumber, setPrNumber] = useState(37613);
  const [action, setAction] = useState('opened');
  const [title, setTitle] = useState('Fix concurrent mode fiber node memory leak on unmount');
  const [author, setAuthor] = useState('acdlite');
  const [deliveryId, setDeliveryId] = useState('deliv-' + Math.random().toString(36).substring(2, 10));
  const [signatureMode, setSignatureMode] = useState<'VALID' | 'INVALID' | 'NONE'>('VALID');

  const [sending, setSending] = useState(false);
  const [response, setResponse] = useState<any>(null);

  const regenerateDeliveryId = () => {
    setDeliveryId('deliv-' + Math.random().toString(36).substring(2, 10));
  };

  const handleSendWebhook = async () => {
    setSending(true);
    setResponse(null);

    const payload = {
      action,
      number: prNumber,
      pull_request: {
        number: prNumber,
        title,
        state: 'open',
        user: { login: author },
        head: { sha: 'f93c812', ref: 'feat/fix-leak' },
        base: { sha: 'e28fa10', ref: 'main' },
      },
      repository: {
        name: repo,
        full_name: `${owner}/${repo}`,
        owner: { login: owner },
      },
      sender: { login: author },
    };

    let signature: string | undefined;
    if (signatureMode === 'VALID') {
      // In production/local, backend default secret is releaseguard-webhook-secret-dev
      signature = 'sha256=VALID_MOCK_SIGNATURE';
    } else if (signatureMode === 'INVALID') {
      signature = 'sha256=bad_signature_deadbeef123456';
    }

    try {
      const res = await api.sendGitHubWebhook(payload, signature, deliveryId);
      setResponse(res);
    } catch (e: any) {
      setResponse({
        status: 500,
        data: { error: e?.message || 'Network error sending webhook' },
      });
    } finally {
      setSending(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Header */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#818cf8', fontSize: '0.85rem', fontWeight: 600 }}>
          <Zap size={16} /> AUTOMATION PIPELINE CONSOLE
        </div>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700, margin: '6px 0 4px' }}>
          GitHub Webhook & Automation Simulator
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '750px' }}>
          Simulate GitHub <code>pull_request</code> webhooks, test HMAC-SHA256 signature verification, verify delivery ID deduplication, and watch Kafka event publishing trigger end-to-end analysis.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '24px' }}>
        {/* Left: Webhook Payload Generator */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 600 }}>Simulate Webhook Event</h2>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                PR Action Event
              </label>
              <select
                value={action}
                onChange={(e) => setAction(e.target.value)}
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  borderRadius: '8px',
                  backgroundColor: 'var(--bg-input)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-main)',
                  fontSize: '0.88rem',
                  outline: 'none',
                }}
              >
                <option value="opened">opened (Trigger initial analysis)</option>
                <option value="synchronize">synchronize (Trigger re-analysis)</option>
                <option value="reopened">reopened (Trigger re-analysis)</option>
                <option value="closed">closed (Skip analysis)</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                Pull Request # Number
              </label>
              <input
                type="number"
                value={prNumber}
                onChange={(e) => setPrNumber(Number(e.target.value))}
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  borderRadius: '8px',
                  backgroundColor: 'var(--bg-input)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-main)',
                  fontSize: '0.88rem',
                  outline: 'none',
                }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                Repository Owner
              </label>
              <input
                type="text"
                value={owner}
                onChange={(e) => setOwner(e.target.value)}
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  borderRadius: '8px',
                  backgroundColor: 'var(--bg-input)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-main)',
                  fontSize: '0.88rem',
                  outline: 'none',
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                Repository Name
              </label>
              <input
                type="text"
                value={repo}
                onChange={(e) => setRepo(e.target.value)}
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  borderRadius: '8px',
                  backgroundColor: 'var(--bg-input)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-main)',
                  fontSize: '0.88rem',
                  outline: 'none',
                }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '14px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                PR Title
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  borderRadius: '8px',
                  backgroundColor: 'var(--bg-input)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-main)',
                  fontSize: '0.88rem',
                  outline: 'none',
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                Author
              </label>
              <input
                type="text"
                value={author}
                onChange={(e) => setAuthor(e.target.value)}
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  borderRadius: '8px',
                  backgroundColor: 'var(--bg-input)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-main)',
                  fontSize: '0.88rem',
                  outline: 'none',
                }}
              />
            </div>
          </div>

          {/* Deduplication & Signature controls */}
          <div
            style={{
              padding: '14px 16px',
              backgroundColor: 'rgba(255, 255, 255, 0.02)',
              borderRadius: '8px',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
            }}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Delivery ID (<code>X-GitHub-Delivery</code>)
                </span>
                <button
                  type="button"
                  onClick={regenerateDeliveryId}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#818cf8',
                    fontSize: '0.75rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                >
                  <RefreshCw size={12} /> New GUID
                </button>
              </div>
              <input
                type="text"
                value={deliveryId}
                onChange={(e) => setDeliveryId(e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 10px',
                  borderRadius: '6px',
                  backgroundColor: 'var(--bg-input)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-main)',
                  fontSize: '0.8rem',
                  fontFamily: 'var(--font-mono)',
                  outline: 'none',
                }}
              />
            </div>

            <div>
              <span style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                HMAC Signature Mode (<code>X-Hub-Signature-256</code>)
              </span>
              <div style={{ display: 'flex', gap: '8px' }}>
                {(['VALID', 'INVALID', 'NONE'] as const).map((m) => (
                  <button
                    key={m}
                    type="button"
                    onClick={() => setSignatureMode(m)}
                    style={{
                      flex: 1,
                      padding: '6px 10px',
                      borderRadius: '6px',
                      border: signatureMode === m ? '1px solid #818cf8' : '1px solid var(--border-subtle)',
                      backgroundColor: signatureMode === m ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                      color: signatureMode === m ? '#818cf8' : 'var(--text-muted)',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    {m === 'VALID' ? 'Valid Secret' : m === 'INVALID' ? 'Bad Signature' : 'No Header'}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <button
            className="btn btn-primary"
            onClick={handleSendWebhook}
            disabled={sending}
            style={{ width: '100%', padding: '12px' }}
          >
            <Send size={16} /> {sending ? 'Dispatching Webhook...' : 'Dispatch Webhook to /api/webhooks/github'}
          </button>
        </div>

        {/* Right: Live Response & Tracking */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 600 }}>Automation Execution Result</h2>

          {!response ? (
            <div
              style={{
                flex: 1,
                minHeight: '260px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--text-dim)',
                textAlign: 'center',
                gap: '8px',
              }}
            >
              <Zap size={32} strokeWidth={1.5} />
              <p style={{ fontSize: '0.9rem' }}>Ready to receive webhook dispatch.</p>
              <span style={{ fontSize: '0.78rem' }}>Click "Dispatch Webhook" to execute.</span>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div
                style={{
                  padding: '16px',
                  borderRadius: '10px',
                  backgroundColor:
                    response.status === 200 || response.status === 202
                      ? 'rgba(16, 185, 129, 0.08)'
                      : 'rgba(244, 63, 94, 0.08)',
                  border:
                    response.status === 200 || response.status === 202
                      ? '1px solid rgba(16, 185, 129, 0.3)'
                      : '1px solid rgba(244, 63, 94, 0.3)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                }}
              >
                {response.status === 200 || response.status === 202 ? (
                  <CheckCircle2 size={24} color="var(--risk-low)" />
                ) : (
                  <AlertTriangle size={24} color="var(--risk-critical)" />
                )}
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>
                    HTTP {response.status} — {response.data?.status || 'OK'}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {response.data?.message || 'Processed by ReleaseGuard backend'}
                  </div>
                </div>
              </div>

              {response.data?.correlationId && (
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Correlation ID:{' '}
                  <span style={{ fontFamily: 'var(--font-mono)', color: '#818cf8' }}>
                    {response.data.correlationId}
                  </span>
                </div>
              )}

              {response.data?.analysisResponse?.prediction && (
                <div
                  style={{
                    padding: '16px',
                    borderRadius: '8px',
                    backgroundColor: 'rgba(255, 255, 255, 0.02)',
                    border: '1px solid var(--border-subtle)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px',
                  }}
                >
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600 }}>
                    Automated ML Prediction
                  </span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className={`badge badge-${response.data.analysisResponse.prediction.riskLevel.toLowerCase()}`}>
                      {response.data.analysisResponse.prediction.riskLevel}
                    </span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem' }}>
                      Score: {(response.data.analysisResponse.prediction.riskScore * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              )}

              {/* Raw JSON viewer */}
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600 }}>
                  Response Payload JSON
                </span>
                <pre
                  style={{
                    marginTop: '6px',
                    padding: '14px',
                    borderRadius: '8px',
                    backgroundColor: 'var(--bg-canvas)',
                    border: '1px solid var(--border-subtle)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.78rem',
                    color: '#818cf8',
                    maxHeight: '200px',
                    overflow: 'auto',
                  }}
                >
                  {JSON.stringify(response.data, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
