import { useEffect, useState } from 'react';
import { fetchCallMetrics, fetchCalls, fetchTranscript, fetchTranscripts } from '../lib/api';
import type {
  CallMetrics,
  CallOutcome,
  CallRecord,
  ToolEvent,
  TranscriptDetail,
  TranscriptEntry,
  TranscriptMeta,
} from '../lib/types';

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
  const [transcripts, setTranscripts] = useState<TranscriptMeta[]>([]);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = () => {
      Promise.all([fetchCallMetrics(), fetchCalls(), fetchTranscripts()])
        .then(([m, c, t]) => {
          if (cancelled) return;
          setMetrics(m);
          setCalls(c);
          setTranscripts(t);
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
        <KpiTile
          label="Response latency"
          value={
            metrics?.median_response_latency_s != null
              ? `${metrics.median_response_latency_s.toFixed(1)}s`
              : '—'
          }
          detail="median, caller stops → agent speaks"
          accent="teal"
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

      <section className="panel">
        <header className="panel__header">
          <h2>Transcripts</h2>
          <span className="state-badge">on-disk record · PII-masked · survives restarts</span>
        </header>
        {transcripts.length === 0 ? (
          <p className="transcript__empty supervisor__empty">
            No transcripts yet. Every call (browser or terminal console) writes a masked JSONL
            transcript the moment it happens — they appear here.
          </p>
        ) : (
          <div className="call-log">
            {transcripts.map((t) => (
              <TranscriptRow key={t.session_id} meta={t} />
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
        {call.channel === 'sip' && <span className="channel-chip">☎ phone</span>}
        {call.step_up_verified && (
          <span
            className="outcome-badge outcome-badge--contained"
            title="Possession-factor step-up passed on this call"
          >
            🛡 step-up
          </span>
        )}
        <span className={`outcome-badge outcome-badge--${call.outcome}`}>
          {OUTCOME_LABELS[call.outcome]}
        </span>
        <span className="call-row__meta">
          {formatDuration(call.duration_seconds)} · {call.tool_calls} tool call
          {call.tool_calls === 1 ? '' : 's'}
          {call.latency && <span> · resp {call.latency.total_median_s.toFixed(1)}s</span>}
          {call.escalation_ref && <span className="mono"> · {call.escalation_ref}</span>}
        </span>
      </summary>
      <div className="call-row__audit">
        {call.latency && (
          <p className="latency-line" title="Per-turn response latency, joined by speech id">
            <b>Latency</b> (median over {call.latency.turns} turn
            {call.latency.turns === 1 ? '' : 's'}): turn detect{' '}
            {call.latency.eou_median_s.toFixed(2)}s · LLM first token{' '}
            {call.latency.llm_ttft_median_s.toFixed(2)}s · TTS first audio{' '}
            {call.latency.tts_ttfb_median_s.toFixed(2)}s → total{' '}
            <b>{call.latency.total_median_s.toFixed(2)}s</b> (p95{' '}
            {call.latency.total_p95_s.toFixed(2)}s)
          </p>
        )}
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

function TranscriptRow({ meta }: { meta: TranscriptMeta }) {
  const [detail, setDetail] = useState<TranscriptDetail | 'loading' | 'error' | null>(null);

  const onToggle = (event: React.SyntheticEvent<HTMLDetailsElement>) => {
    if (!event.currentTarget.open || detail !== null) return;
    setDetail('loading');
    fetchTranscript(meta.session_id)
      .then(setDetail)
      .catch(() => setDetail('error'));
  };

  const when = new Date(meta.modified_at);
  return (
    <details className="call-row" onToggle={onToggle}>
      <summary>
        <span className="mono call-row__time">
          {meta.date} {when.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
        <span className="call-row__who">
          {meta.customer ?? 'Unverified caller'}
          <span className="call-row__scenario mono"> · {meta.session_id}</span>
        </span>
        {meta.channel === 'sip' && <span className="channel-chip">☎ phone</span>}
        {meta.escalated && <span className="outcome-badge outcome-badge--escalated">Escalated</span>}
        {!meta.ended && <span className="outcome-badge">No clean end</span>}
        <span className="call-row__meta">
          {meta.duration_seconds != null && <>{formatDuration(meta.duration_seconds)} · </>}
          {meta.messages} turns · {meta.tool_events} tool events
        </span>
      </summary>
      <div className="call-row__audit">
        {detail === 'loading' && <p className="transcript__empty">Loading transcript…</p>}
        {detail === 'error' && (
          <p className="transcript__empty">Could not load this transcript. Try again.</p>
        )}
        {detail !== null && typeof detail === 'object' && (
          <ol className="ts-lines">
            {detail.entries.map((entry, index) => (
              <TranscriptLine key={index} entry={entry} />
            ))}
          </ol>
        )}
      </div>
    </details>
  );
}

function TranscriptLine({ entry }: { entry: TranscriptEntry }) {
  if (entry.kind === 'message') {
    const caller = entry.role === 'user';
    return (
      <li className={`ts-msg ${caller ? 'ts-msg--caller' : 'ts-msg--agent'}`}>
        <span className="ts-msg__who">{caller ? 'Caller' : 'Agent'}</span>
        <span className="ts-msg__text">
          {entry.content}
          {entry.interrupted && <em className="ts-msg__interrupted"> (interrupted)</em>}
        </span>
      </li>
    );
  }
  if (entry.kind === 'tool_event') {
    return (
      <li className={`audit-line audit-line--${entry.type ?? 'tool_event'}`}>
        <span className="audit-line__type">{(entry.type ?? 'tool event').replaceAll('_', ' ')}</span>
        {entry.tool && <span className="mono audit-line__tool">{entry.tool}</span>}
        {entry.duration_ms != null && (
          <span className="audit-line__time mono">{entry.duration_ms} ms</span>
        )}
        {entry.result_summary && (
          <span className="audit-line__summary">{entry.result_summary}</span>
        )}
        {entry.error && <span className="activity-card__error">{entry.error}</span>}
      </li>
    );
  }
  if (entry.kind === 'session_end') {
    return (
      <li className="ts-end mono">
        call ended · {entry.duration_seconds != null && <>{formatDuration(entry.duration_seconds)} · </>}
        {entry.verified_customer ? `verified: ${entry.verified_customer}` : 'unverified'}
        {entry.escalated ? ' · escalated' : ''}
      </li>
    );
  }
  return null;
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return mins > 0 ? `${mins}m ${secs.toString().padStart(2, '0')}s` : `${secs}s`;
}
