import { useEffect, useState } from 'react';
import { fetchScenarios } from '../lib/api';
import type { ScenarioInfo } from '../lib/types';

interface Props {
  onStart: (scenario: ScenarioInfo) => void;
  starting: boolean;
}

export function ScenarioPicker({ onStart, starting }: Props) {
  const [scenarios, setScenarios] = useState<ScenarioInfo[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchScenarios()
      .then(setScenarios)
      .catch(() => setError('Could not reach the mock bank backend on :8000. Is it running?'));
  }, []);

  if (error) return <div className="notice notice--error">{error}</div>;
  if (!scenarios) return <div className="notice">Loading demo scenarios…</div>;

  return (
    <div className="picker">
      <div className="picker__intro">
        <h1>Start a demo call</h1>
        <p>
          Pick a customer scenario. You will speak to the AI agent as that customer — their account
          details appear on a crib card during the call.
        </p>
      </div>
      <div className="picker__grid">
        {scenarios.map((scenario) => (
          <button
            key={scenario.id}
            className="scenario-card"
            disabled={starting}
            onClick={() => onStart(scenario)}
          >
            <span className="scenario-card__title">{scenario.title}</span>
            <span className="scenario-card__customer">{scenario.customer_name}</span>
            <span className="scenario-card__description">{scenario.description}</span>
            <span className="scenario-card__cta">{starting ? 'Connecting…' : 'Start call'}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
