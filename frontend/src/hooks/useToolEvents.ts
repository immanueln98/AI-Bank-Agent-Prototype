import { useRoomContext } from '@livekit/components-react';
import { useEffect, useState } from 'react';
import { TOOL_EVENTS_TOPIC, type ToolEvent } from '../lib/types';

/**
 * Live feed of the agent's tool activity: JSON ToolEvents streamed by the
 * Python agent over a LiveKit text stream on the `tool-events` topic.
 */
export function useToolEvents(): ToolEvent[] {
  const room = useRoomContext();
  const [events, setEvents] = useState<ToolEvent[]>([]);

  useEffect(() => {
    if (!room) return;
    room.registerTextStreamHandler(TOOL_EVENTS_TOPIC, (reader) => {
      void reader.readAll().then((text) => {
        try {
          const event = JSON.parse(text) as ToolEvent;
          setEvents((previous) => [...previous, event]);
        } catch {
          // Malformed event: drop it rather than break the panel.
        }
      });
    });
    return () => room.unregisterTextStreamHandler(TOOL_EVENTS_TOPIC);
  }, [room]);

  return events;
}

export type ActivityStatus = 'running' | 'done' | 'failed';

export interface ActivityCard {
  key: string;
  kind: 'tool' | 'identity' | 'escalation' | 'lockout';
  tool: string | null;
  status: ActivityStatus;
  args: Record<string, unknown> | null;
  summary: string | null;
  error: string | null;
  durationMs: number | null;
  ts: string;
}

/** Merge started/finished/failed pairs (correlated by id) into panel cards. */
export function toActivityCards(events: ToolEvent[]): ActivityCard[] {
  const cards: ActivityCard[] = [];
  const byId = new Map<string, ActivityCard>();

  for (const event of events) {
    switch (event.type) {
      case 'tool_call_started': {
        const card: ActivityCard = {
          key: event.id,
          kind: 'tool',
          tool: event.tool,
          status: 'running',
          args: event.args_masked,
          summary: null,
          error: null,
          durationMs: null,
          ts: event.ts,
        };
        byId.set(event.id, card);
        cards.push(card);
        break;
      }
      case 'tool_call_finished':
      case 'tool_call_failed': {
        const card = byId.get(event.id);
        if (card) {
          card.status = event.type === 'tool_call_finished' ? 'done' : 'failed';
          card.summary = event.result_summary;
          card.error = event.error;
          card.durationMs = event.duration_ms;
        }
        break;
      }
      case 'identity_verified':
      case 'escalation':
      case 'security_lockout':
        cards.push({
          key: event.id,
          kind:
            event.type === 'identity_verified'
              ? 'identity'
              : event.type === 'escalation'
                ? 'escalation'
                : 'lockout',
          tool: null,
          status: 'done',
          args: null,
          summary: event.result_summary,
          error: null,
          durationMs: null,
          ts: event.ts,
        });
        break;
    }
  }
  return cards;
}
