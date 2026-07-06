import type { ScenarioInfo, TokenResponse } from './types';

const BACKEND_URL: string =
  (import.meta.env.VITE_BACKEND_URL as string | undefined) ?? 'http://localhost:8000';

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

export function fetchToken(scenario: string): Promise<TokenResponse> {
  return request<TokenResponse>('/api/v1/livekit/token', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ scenario }),
  });
}
