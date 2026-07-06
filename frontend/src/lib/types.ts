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
  | 'escalation'
  | 'security_lockout';

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

export type CallOutcome = 'contained' | 'escalated' | 'verification_failed' | 'abandoned';

/** Mirrors CallRecord in shared/src/bankagent_shared/models.py. */
export interface CallRecord {
  session_id: string;
  room: string;
  scenario: string | null;
  started_at: string;
  ended_at: string;
  duration_seconds: number;
  outcome: CallOutcome;
  verified: boolean;
  customer_first_name: string | null;
  account_masked: string | null;
  failed_verification_attempts: number;
  locked_out: boolean;
  escalated: boolean;
  escalation_ref: string | null;
  tools_used: string[];
  tool_calls: number;
  tool_failures: number;
  events: ToolEvent[];
  usage_summary: string | null;
}

/** Mirrors CallMetrics in shared/src/bankagent_shared/models.py. */
export interface CallMetrics {
  total_calls: number;
  contained: number;
  escalated: number;
  verification_failed: number;
  abandoned: number;
  lockouts: number;
  containment_rate: number | null;
  avg_duration_seconds: number | null;
  avg_tool_calls: number | null;
}
