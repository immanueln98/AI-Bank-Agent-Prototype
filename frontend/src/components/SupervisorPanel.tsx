import { useEffect, useState } from 'react';
import { fetchCallMetrics, fetchCalls } from '../lib/api';
import type { CallMetrics, CallOutcome, CallRecord, ToolEvent } from '../lib/types';

const POLL_MS = 4000;

const OUTCOME_LABELS: Record<CallOutcome, string> = {
  contained: 'Contained by AI',
  escalated: 'Escalated to human',
  verification_failed: 'Verification failed',
  abandoned: 'Abandoned',
};

/**
 * The contact-centre manager's view: live KPIs (containment, handle time,
 * escalations) plus a per-call drill-down into the PII-masked audit trail.
 * Same numbers a bank already runs its human call centre on.
 */
export function SupervisorPanel() {
  const [metrics, setMetrics] = useState<CallMetrics | null>(null);
  const [calls, setCalls] = useState<CallRecord[]>([]);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = () => {
      Promise.all([fetchCallMetrics(), fetchCalls()])
        .then(([m, c]) => {
          if (cancelled) return;
          setMetrics(m);
          setCalls(c);
          setError(false);
        })
        .catch(() => !cancelled && setError(true));
    };
    load();
    const timer = setInterval(load, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  return (
    <div className="supervisor">
      {error && (
        <div className="notice notice--error">
          Could not reach the backend. Is <code>make run-backend</code> up?
        </div>
      )}

      <div className="kpi-grid">
        <KpiTile
          label="Calls handled"
          value={metrics ? String(metrics.total_calls) : '—'}
          detail="this session"
        />
        <KpiTile
          label="Containment rate"
          value={
            metrics?.containment_rate != null
              ? `${Math.round(metrics.containment_rate * 100)}%`
              : '—'
          }
          detail="resolved without a human"
          accent="teal"
        />
        <KpiTile
          label="Avg handle time"
          value={
            metrics?.avg_duration_seconds != null
              ? formatDuration(metrics.avg_duration_seconds)
              : '—'
          }
          detail="per call"
        />
        <KpiTile
          label="Escalations"
          value={metrics ? String(metrics.escalated) : '—'}
          detail="handed to consultants"
          accent="amber"
        />
        <KpiTile
          label="Security lockouts"
          value={metrics ? String(metrics.lockouts) : '—'}
          detail="3× failed verification"
          accent={metrics && metrics.lockouts > 0 ? 'red' : undefined}
        />
      </div>

      <section className="panel">
        <header className="panel__header">
          <h2>Call log</h2>
          <span className="state-badge">auto-refreshes · PII-masked</span>
        </header>
        {calls.length === 0 ? (
          <p className="transcript__empty supervisor__empty">
            No calls yet. Switch to the Console view, run a scenario, and hang up — the call
            record lands here with its full audit trail.
          </p>
        ) : (
          <div className="call-log">
            {calls.map((call) => (
              <CallRow key={call.session_id} call={call} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function KpiTile({
  label,
  value,
  detail,
  accent,
}: {
  label: string;
  value: string;
  detail: string;
  accent?: 'teal' | 'amber' | 'red';
}) {
  return (
    <div className={`kpi-tile ${accent ? `kpi-tile--${accent}` : ''}`}>
      <span className="kpi-tile__label">{label}</span>
      <span className="kpi-tile__value">{value}</span>
      <span className="kpi-tile__detail">{detail}</span>
    </div>
  );
}

function CallRow({ call }: { call: CallRecord }) {
  const started = new Date(call.started_at);
  return (
    <details className="call-row">
      <summary>
        <span className="mono call-row__time">
          {started.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
        <span className="call-row__who">
          {call.customer_first_name ?? 'Unverified caller'}
          {call.scenario && <span className="call-row__scenario"> · {call.scenario}</span>}
        </span>
        <span className={`outcome-badge outcome-badge--${call.outcome}`}>
          {OUTCOME_LABELS[call.outcome]}
        </span>
        <span className="call-row__meta">
          {formatDuration(call.duration_seconds)} · {call.tool_calls} tool call
          {call.tool_calls === 1 ? '' : 's'}
          {call.escalation_ref && <span className="mono"> · {call.escalation_ref}</span>}
        </span>
      </summary>
      <div className="call-row__audit">
        <h3>Audit trail</h3>
        {call.events.length === 0 ? (
          <p className="transcript__empty">No tool activity on this call.</p>
        ) : (
          <ol>
            {call.events.map((event, index) => (
              <AuditLine key={`${event.id}-${index}`} event={event} />
            ))}
          </ol>
        )}
        {call.usage_summary && (
          <p className="call-row__usage mono" title="LLM/STT/TTS usage for cost tracking">
            {call.usage_summary}
          </p>
        )}
      </div>
    </details>
  );
}

function AuditLine({ event }: { event: ToolEvent }) {
  const time = new Date(event.ts).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
  return (
    <li className={`audit-line audit-line--${event.type}`}>
      <span className="mono audit-line__time">{time}</span>
      <span className="audit-line__type">{event.type.replaceAll('_', ' ')}</span>
      {event.tool && <span className="mono audit-line__tool">{event.tool}</span>}
      {event.args_masked && Object.keys(event.args_masked).length > 0 && (
        <code className="audit-line__args">
          {Object.entries(event.args_masked)
            .map(([key, value]) => `${key}=${String(value)}`)
            .join(' ')}
        </code>
      )}
      {event.result_summary && <span className="audit-line__summary">{event.result_summary}</span>}
      {event.error && <span className="activity-card__error">{event.error}</span>}
    </li>
  );
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return mins > 0 ? `${mins}m ${secs.toString().padStart(2, '0')}s` : `${secs}s`;
}
