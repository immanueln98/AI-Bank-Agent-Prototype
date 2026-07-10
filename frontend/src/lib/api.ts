import type {
  CallMetrics,
  CallRecord,
  ScenarioInfo,
  StepUpChallenge,
  TokenResponse,
  TranscriptDetail,
  TranscriptMeta,
} from './types';

// Default is same-origin: the Vite dev server proxies /api to the backend
// (see vite.config.ts), which is what lets one ngrok tunnel share the whole
// demo. Docker/static builds pass VITE_BACKEND_URL explicitly instead.
const BACKEND_URL: string = (import.meta.env.VITE_BACKEND_URL as string | undefined) ?? '';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BACKEND_URL}${path}`, init);
  if (!response.ok) {
    throw new Error(`${init?.method ?? 'GET'} ${path} failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

export function fetchScenarios(): Promise<ScenarioInfo[]> {
  return request<ScenarioInfo[]>('/api/v1/demo/scenarios');
}

export function fetchCalls(): Promise<CallRecord[]> {
  return request<CallRecord[]>('/api/v1/calls');
}

export function fetchCallMetrics(): Promise<CallMetrics> {
  return request<CallMetrics>('/api/v1/calls/metrics');
}

export function fetchTranscripts(): Promise<TranscriptMeta[]> {
  return request<TranscriptMeta[]>('/api/v1/transcripts');
}

export function fetchTranscript(sessionId: string): Promise<TranscriptDetail> {
  return request<TranscriptDetail>(`/api/v1/transcripts/${encodeURIComponent(sessionId)}`);
}

export function fetchStepUpChallenge(): Promise<StepUpChallenge | null> {
  return request<StepUpChallenge | null>('/api/v1/demo/stepup/latest');
}

export function fetchToken(scenario: string): Promise<TokenResponse> {
  return request<TokenResponse>('/api/v1/livekit/token', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ scenario }),
  });
}
