import { toActivityCards, useToolEvents, type ActivityCard } from '../hooks/useToolEvents';
import { fetchStepUpChallenge } from '../lib/api';
import type { ScenarioInfo, StepUpChallenge } from '../lib/types';
import { useEffect, useRef, useState } from 'react';

const TOOL_LABELS: Record<string, string> = {
  verify_identity: 'Verify identity',
  get_customer_profile: 'Fetch customer profile',
  get_recent_transactions: 'Fetch recent transactions',
  send_step_up_code: 'Send step-up code',
  verify_step_up_code: 'Verify step-up code',
  report_card_lost: 'Report card lost',
  dispute_transaction: 'Dispute transaction',
  search_faq: 'Search FAQ',
  escalate_to_human: 'Escalate to human',
};

/**
 * "What the agent is doing" - the proof that every answer is grounded in a
 * real (mock) system call, not hallucinated.
 */
export function ActivityPanel({ scenario }: { scenario: ScenarioInfo }) {
  const events = useToolEvents();
  const cards = toActivityCards(events);
  const identity = [...cards].reverse().find((c) => c.kind === 'identity');
  const escalation = cards.find((c) => c.kind === 'escalation');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [cards.length]);

  return (
    <section className="panel activity-panel">
      <header className="panel__header">
        <h2>Agent activity</h2>
        <span className={`id-badge ${identity ? 'id-badge--verified' : ''}`}>
          {identity
            ? identity.summary?.replace('Identity verified: ', 'Verified: ')
            : 'Unverified caller'}
        </span>
      </header>

      {escalation && (
        <div className="escalation-banner">
          <strong>Escalated to human consultant</strong>
          <span>{escalation.summary}</span>
        </div>
      )}

      <CribCard scenario={scenario} />
      <CustomerPhone />

      <div className="activity-panel__feed">
        {cards.length === 0 && (
          <p className="transcript__empty">
            Tool calls appear here live as the agent works — verification, lookups, actions.
          </p>
        )}
        {cards.map((card) => (
          <ActivityCardView key={card.key} card={card} />
        ))}
        <div ref={bottomRef} />
      </div>
    </section>
  );
}

function CribCard({ scenario }: { scenario: ScenarioInfo }) {
  return (
    <details className="crib-card" open>
      <summary>
        Presenter crib card — {scenario.customer_name} ({scenario.title})
      </summary>
      <dl>
        <div>
          <dt>Account number</dt>
          <dd className="mono">{scenario.account_number}</dd>
        </div>
        <div>
          <dt>ID ends in</dt>
          <dd className="mono">{scenario.id_last4}</dd>
        </div>
      </dl>
      <ul>
        {scenario.suggested_lines.map((line) => (
          <li key={line}>“{line}”</li>
        ))}
      </ul>
    </details>
  );
}

/** Simulates the customer's registered device: when the agent sends a
 * step-up code, the "banking app notification" appears here. A real
 * deployment has no equivalent — the code exists only on the real phone. */
function CustomerPhone() {
  const [challenge, setChallenge] = useState<StepUpChallenge | null>(null);

  useEffect(() => {
    let cancelled = false;
    const poll = () => {
      fetchStepUpChallenge()
        .then((c) => !cancelled && setChallenge(c))
        .catch(() => !cancelled && setChallenge(null));
    };
    poll();
    const timer = setInterval(poll, 2500);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  if (!challenge) return null;
  return (
    <div className="phone-sim" aria-live="polite">
      <span className="phone-sim__label">📱 Customer's phone (simulated)</span>
      <div className="phone-sim__notification">
        <span className="phone-sim__app">Meridian Bank app</span>
        <span>
          Hi {challenge.customer_first_name} — your one-time approval code is{' '}
          <b className="mono phone-sim__code">{challenge.code}</b>. Never share it with anyone
          except on your own call with the bank.
        </span>
      </div>
    </div>
  );
}

function ActivityCardView({ card }: { card: ActivityCard }) {
  if (card.kind === 'identity') {
    return (
      <div className="activity-card activity-card--identity">
        <span className="activity-card__icon">✓</span>
        <div>
          <span className="activity-card__title">Identity verified</span>
          <span className="activity-card__summary">{card.summary}</span>
        </div>
      </div>
    );
  }
  if (card.kind === 'escalation') {
    return (
      <div className="activity-card activity-card--escalation">
        <span className="activity-card__icon">⤴</span>
        <div>
          <span className="activity-card__title">Handed off to human</span>
          <span className="activity-card__summary">{card.summary}</span>
        </div>
      </div>
    );
  }
  if (card.kind === 'stepup') {
    return (
      <div className="activity-card activity-card--identity">
        <span className="activity-card__icon">🛡</span>
        <div>
          <span className="activity-card__title">Step-up verified</span>
          <span className="activity-card__summary">{card.summary}</span>
        </div>
      </div>
    );
  }
  if (card.kind === 'lockout') {
    return (
      <div className="activity-card activity-card--failed">
        <span className="activity-card__icon">🔒</span>
        <div>
          <span className="activity-card__title">Security lockout</span>
          <span className="activity-card__summary">{card.summary}</span>
        </div>
      </div>
    );
  }
  return (
    <div className={`activity-card activity-card--${card.status}`}>
      <span className="activity-card__icon">
        {card.status === 'running' ? (
          <span className="spinner" />
        ) : card.status === 'done' ? (
          '⚙'
        ) : (
          '⚠'
        )}
      </span>
      <div>
        <span className="activity-card__title">
          {TOOL_LABELS[card.tool ?? ''] ?? card.tool}
          {card.durationMs !== null && (
            <span className="activity-card__duration">{card.durationMs} ms</span>
          )}
        </span>
        {card.args && Object.keys(card.args).length > 0 && (
          <code className="activity-card__args">
            {Object.entries(card.args)
              .map(([key, value]) => `${key}=${String(value)}`)
              .join('  ')}
          </code>
        )}
        {card.summary && <span className="activity-card__summary">{card.summary}</span>}
        {card.error && <span className="activity-card__error">{card.error}</span>}
      </div>
    </div>
  );
}
