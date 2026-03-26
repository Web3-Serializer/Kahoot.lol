const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

const h = (): Record<string, string> => {
  const jwt = localStorage.getItem('jwt');
  return { 'Content-Type': 'application/json', ...(jwt ? { Authorization: `Bearer ${jwt}` } : {}) };
};
async function r<T>(m: string, p: string, b?: unknown): Promise<T> {
  const res = await fetch(`${API}${p}`, { method: m, headers: h(), body: b ? JSON.stringify(b) : undefined });
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || `${res.status}`); }
  return res.json();
}
export const api = {
  register: (u: string) => r<any>('POST', '/auth/register', { username: u }),
  login: (t: string) => r<any>('POST', '/auth/login', { token: t }),
  me: () => r<any>('GET', '/user/me'),
  start: (c: any) => r<any>('POST', '/game/start', c),
  stop: (id: string) => r<any>('POST', `/game/${id}/stop`),
  status: (id: string) => r<any>('GET', `/game/${id}/status`),
  submit2fa: (id: string, seq: number[]) => r<any>('POST', `/game/${id}/2fa`, { sequence: seq }),
  sessions: () => r<any>('GET', '/game/sessions'),
  ollamaStatus: (model?: string) => r<any>('GET', `/ollama/status${model ? `?model=${model}` : ''}`),
  adminUsers: () => r<any>('GET', '/admin/users'),
  adminAddCredits: (uid: string, a: number) => r<any>('POST', '/admin/credits/add', { user_id: uid, amount: a }),
  adminDelete: (uid: string) => r<any>('POST', '/admin/delete', { user_id: uid }),
  adminPromote: (uid: string) => r<any>('POST', '/admin/promote', { user_id: uid }),
  adminInit: () => r<any>('POST', '/admin/init'),
};
