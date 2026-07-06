/**
 * TypeScript mirrors of the backend/agent contracts.
 *
 * ToolEvent mirrors shared/src/bankagent_shared/events.py - keep in sync by
 * hand (documented at the top of both files).
 */

export const TOOL_EVENTS_TOPIC = 'tool-events';

export type ToolEventType =
  | 'tool_call_started'
  | 'tool_call_finished'
  | 'tool_call_failed'
  | 'identity_verified'
  | 'escalation';

export interface ToolEvent {
  type: ToolEventType;
  id: string;
  tool: string | null;
  args_masked: Record<string, unknown> | null;
  result_summary: string | null;
  error: string | null;
  duration_ms: number | null;
  ts: string;
}

export interface ScenarioInfo {
  id: string;
  title: string;
  customer_name: string;
  account_number: string;
  id_last4: string;
  description: string;
  suggested_lines: string[];
}

export interface TokenResponse {
  url: string;
  token: string;
  room: string;
}
