import { toActivityCards, useToolEvents, type ActivityCard } from '../hooks/useToolEvents';
import type { ScenarioInfo } from '../lib/types';
import { useEffect, useRef } from 'react';

const TOOL_LABELS: Record<string, string> = {
  verify_identity: 'Verify identity',
  get_customer_profile: 'Fetch customer profile',
  get_recent_transactions: 'Fetch recent transactions',
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
