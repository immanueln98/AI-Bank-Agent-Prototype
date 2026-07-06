import { LiveKitRoom, RoomAudioRenderer, StartAudio } from '@livekit/components-react';
import { useState } from 'react';
import { ActivityPanel } from './components/ActivityPanel';
import { CallPanel } from './components/CallPanel';
import { ScenarioPicker } from './components/ScenarioPicker';
import { SupervisorPanel } from './components/SupervisorPanel';
import { fetchToken } from './lib/api';
import type { ScenarioInfo, TokenResponse } from './lib/types';

interface ActiveCall {
  scenario: ScenarioInfo;
  connection: TokenResponse;
}

type View = 'console' | 'supervisor';

export default function App() {
  const [view, setView] = useState<View>('console');
  const [call, setCall] = useState<ActiveCall | null>(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startCall = (scenario: ScenarioInfo) => {
    setStarting(true);
    setError(null);
    fetchToken(scenario.id)
      .then((connection) => setCall({ scenario, connection }))
      .catch(() =>
        setError('Could not get a call token. Check the backend and your LiveKit credentials.'),
      )
      .finally(() => setStarting(false));
  };

  return (
    <div className="app">
      <header className="app__header">
        <div className="brand">
          <span className="brand__mark">M</span>
          <div>
            <span className="brand__name">Meridian Bank</span>
            <span className="brand__sub">AI Voice Agent — Demo Console</span>
          </div>
        </div>
        <nav className="view-switch" aria-label="View">
          <button
            className={`view-switch__btn ${view === 'console' ? 'view-switch__btn--active' : ''}`}
            onClick={() => setView('console')}
          >
            Console
          </button>
          <button
            className={`view-switch__btn ${view === 'supervisor' ? 'view-switch__btn--active' : ''}`}
            onClick={() => setView('supervisor')}
          >
            Supervisor
          </button>
        </nav>
        {call && (
          <span className="room-chip mono" title="LiveKit room">
            {call.connection.room}
          </span>
        )}
      </header>

      <main className="app__main">
        {view === 'supervisor' && <SupervisorPanel />}
        {/* The console stays mounted (hidden) while the supervisor view is
            open so an in-progress call keeps running. */}
        <div style={view === 'console' ? undefined : { display: 'none' }}>
          {error && <div className="notice notice--error">{error}</div>}
          {!call ? (
            <ScenarioPicker onStart={startCall} starting={starting} />
          ) : (
            <LiveKitRoom
              serverUrl={call.connection.url}
              token={call.connection.token}
              connect
              audio
              video={false}
              onDisconnected={() => setCall(null)}
              className="console"
            >
              <CallPanel onEnd={() => setCall(null)} />
              <ActivityPanel scenario={call.scenario} />
              <RoomAudioRenderer />
              <StartAudio label="Click to enable audio" className="btn btn--primary start-audio" />
            </LiveKitRoom>
          )}
        </div>
      </main>

      <footer className="app__footer">
        Proof of concept — mock data only. The agent is grounded in the activity feed on the right:
        every answer traces to a system call. The Supervisor view shows the call log and KPIs a
        contact-centre manager would see.
      </footer>
    </div>
  );
}
