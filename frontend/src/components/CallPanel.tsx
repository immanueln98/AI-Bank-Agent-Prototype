import {
  BarVisualizer,
  useLocalParticipant,
  useRoomContext,
  useVoiceAssistant,
} from '@livekit/components-react';
import { TranscriptView } from './TranscriptView';

const STATE_LABELS: Record<string, string> = {
  disconnected: 'Agent offline',
  connecting: 'Connecting…',
  initializing: 'Agent starting…',
  listening: 'Listening',
  thinking: 'Thinking…',
  speaking: 'Speaking',
};

export function CallPanel({ onEnd }: { onEnd: () => void }) {
  const room = useRoomContext();
  const { state, audioTrack } = useVoiceAssistant();
  const { isMicrophoneEnabled, localParticipant } = useLocalParticipant();

  const toggleMic = () => {
    void localParticipant.setMicrophoneEnabled(!isMicrophoneEnabled);
  };
  const endCall = () => {
    void room.disconnect().then(onEnd);
  };

  return (
    <section className="panel call-panel">
      <header className="panel__header">
        <h2>Live call</h2>
        <span className={`state-badge state-badge--${state}`}>{STATE_LABELS[state] ?? state}</span>
      </header>

      <div className="call-panel__viz" data-lk-theme="default">
        <BarVisualizer state={state} trackRef={audioTrack} barCount={5} />
      </div>

      <div className="call-panel__controls">
        <button
          className={`btn ${isMicrophoneEnabled ? 'btn--secondary' : 'btn--danger'}`}
          onClick={toggleMic}
        >
          {isMicrophoneEnabled ? 'Mute mic' : 'Unmute mic'}
        </button>
        <button className="btn btn--danger" onClick={endCall}>
          End call
        </button>
      </div>

      <TranscriptView />
    </section>
  );
}
