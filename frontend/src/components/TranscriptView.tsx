import { useTranscriptions, useVoiceAssistant } from '@livekit/components-react';
import { useEffect, useRef } from 'react';

/**
 * Live transcript of both sides. Interim/final segment merging is handled by
 * useTranscriptions (deduped on lk.segment_id), so this just renders in order.
 */
export function TranscriptView() {
  const transcriptions = useTranscriptions();
  const { agent } = useVoiceAssistant();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcriptions.length]);

  const sorted = [...transcriptions].sort(
    (a, b) => a.streamInfo.timestamp - b.streamInfo.timestamp,
  );

  return (
    <div className="transcript">
      <h3 className="transcript__title">Transcript</h3>
      <div className="transcript__scroll">
        {sorted.length === 0 && (
          <p className="transcript__empty">Say hello — the conversation will appear here.</p>
        )}
        {sorted.map((segment) => {
          const isAgent = agent && segment.participantInfo.identity === agent.identity;
          const isFinal = segment.streamInfo.attributes?.['lk.transcription_final'] === 'true';
          return (
            <div
              key={segment.streamInfo.id}
              className={`bubble ${isAgent ? 'bubble--agent' : 'bubble--caller'} ${
                isFinal ? '' : 'bubble--interim'
              }`}
            >
              <span className="bubble__speaker">{isAgent ? 'Kea (AI agent)' : 'Caller'}</span>
              <span className="bubble__text">{segment.text}</span>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
