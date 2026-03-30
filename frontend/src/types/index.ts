export interface AgentMessage {
  index: number;
  role: string;
  content: string;
  type: 'user' | 'agent';
}

export interface AgentStatus {
  status: 'idle' | 'starting' | 'thinking' | 'running' | 'completed' | 'error';
  message: string;
  created_files?: string[];
}

export interface FileInfo {
  path: string;
  content: string;
  workspace: string;
}

export interface FileListInfo {
  files: string[];
  workspace: string;
}

export interface SSEEvent {
  type: string;
  data: Record<string, unknown>;
}

export interface AgentResult {
  result?: {
    messages?: AgentMessage[];
    [key: string]: unknown;
  };
  run_url?: string;
  share_url?: string;
}
