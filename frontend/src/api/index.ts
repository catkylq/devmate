import type { AgentMessage, AgentStatus, FileInfo, FileListInfo, SSEEvent } from '../types';

const API_BASE = '/api';

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

export const api = {
  healthz: () => fetchJSON<{ ok: boolean }>(`${API_BASE}/healthz`),
  
  listWorkspace: () => fetchJSON<FileListInfo>(`${API_BASE}/workspace`),
  
  readFile: (filePath: string) => fetchJSON<FileInfo>(`${API_BASE}/workspace/${filePath}`),
  
  createFile: (path: string, content: string = '') =>
    fetchJSON<{ success: boolean; path: string }>(`${API_BASE}/workspace`, {
      method: 'POST',
      body: JSON.stringify({ path, content }),
    }),
  
  updateFile: (path: string, content: string) =>
    fetchJSON<{ success: boolean; path: string }>(`${API_BASE}/workspace/${path}`, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    }),
  
  deleteFile: (path: string) =>
    fetchJSON<{ success: boolean; path: string }>(`${API_BASE}/workspace/${path}`, {
      method: 'DELETE',
    }),
  
  runAgent: (prompt: string) =>
    fetchJSON<{
      result?: unknown;
      run_url?: string;
      share_url?: string;
    }>(`${API_BASE}/run`, {
      method: 'POST',
      body: JSON.stringify({ prompt }),
    }),
};

export interface AgentStreamCallbacks {
  onStatus: (status: AgentStatus) => void;
  onMessage: (message: AgentMessage) => void;
  onFilesBefore: (files: string[]) => void;
  onFilesAfter: (files: string[], created: string[]) => void;
  onTrace: (url: string) => void;
  onTraceShare: (url: string) => void;
  onError: (error: string) => void;
  onComplete: () => void;
}

export async function runAgentStream(
  prompt: string,
  callbacks: AgentStreamCallbacks
): Promise<void> {
  const response = await fetch(`${API_BASE}/run/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt }),
  });

  if (!response.ok) {
    callbacks.onError(`HTTP ${response.status}: ${response.statusText}`);
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    callbacks.onError('No response body');
    return;
  }

  const decoder = new TextDecoder();
  let buffer = '';
  let eventType = '';
  let eventData = '';

  const processEvent = () => {
    if (!eventType || !eventData) return;
    
    let data: Record<string, unknown>;
    try {
      data = JSON.parse(eventData);
    } catch {
      return;
    }

    const event: SSEEvent = { type: eventType, data };
    
    switch (eventType) {
      case 'status':
        callbacks.onStatus(data as unknown as AgentStatus);
        break;
      case 'message':
        callbacks.onMessage(data as unknown as AgentMessage);
        break;
      case 'files_before':
        callbacks.onFilesBefore((data.files as string[]) || []);
        break;
      case 'files_after':
        callbacks.onFilesAfter(
          (data.files as string[]) || [],
          (data.created as string[]) || []
        );
        break;
      case 'trace':
        callbacks.onTrace((data.url as string) || '');
        break;
      case 'trace_share':
        callbacks.onTraceShare((data.url as string) || '');
        break;
      case 'error':
        callbacks.onError((data.error as string) || 'Unknown error');
        break;
    }
  };

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('event: ')) {
          eventType = line.slice(7).trim();
        } else if (line.startsWith('data: ')) {
          eventData = line.slice(6);
        } else if (line === '') {
          processEvent();
          eventType = '';
          eventData = '';
        }
      }
    }

    if (eventType && eventData) {
      processEvent();
    }

    callbacks.onComplete();
  } catch (err) {
    callbacks.onError(err instanceof Error ? err.message : 'Stream error');
  }
}
