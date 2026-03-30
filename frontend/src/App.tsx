import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Send, Bot, Cpu, FolderTree, ExternalLink } from 'lucide-react';
import { AgentFlow } from './components/AgentFlow';
import { FileManager } from './components/FileManager';
import { runAgentStream, api } from './api';
import type { AgentStatus, AgentMessage } from './types';
import './styles/App.css';

type TabType = 'flow' | 'files';

function App() {
  const [prompt, setPrompt] = useState('');
  const [activeTab, setActiveTab] = useState<TabType>('flow');
  const [isRunning, setIsRunning] = useState(false);
  const [status, setStatus] = useState<AgentStatus>({
    status: 'idle',
    message: '',
  });
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [createdFiles, setCreatedFiles] = useState<string[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [traceUrl, setTraceUrl] = useState<string>('');
  const [traceShareUrl, setTraceShareUrl] = useState<string>('');

  const checkConnection = useCallback(async () => {
    try {
      await api.healthz();
      setIsConnected(true);
    } catch {
      setIsConnected(false);
    }
  }, []);

  useEffect(() => {
    checkConnection();
    const interval = setInterval(checkConnection, 10000);
    return () => clearInterval(interval);
  }, [checkConnection]);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isRunning) return;

    setIsRunning(true);
    setError(null);
    setStatus({ status: 'starting', message: '启动中...' });
    setMessages([]);
    setCreatedFiles([]);
    setTraceUrl('');
    setTraceShareUrl('');

    try {
      await runAgentStream(prompt, {
        onStatus: (newStatus) => {
          setStatus(newStatus);
          if (newStatus.created_files) {
            setCreatedFiles(prev => [...new Set([...prev, ...newStatus.created_files!])]);
          }
        },
        onMessage: (msg) => {
          setMessages(prev => [...prev, msg]);
        },
        onFilesBefore: (files) => {
          console.log('Files before:', files);
        },
        onFilesAfter: (files, created) => {
          setCreatedFiles(created);
        },
        onTrace: (url) => {
          setTraceUrl(url);
        },
        onTraceShare: (url) => {
          setTraceShareUrl(url);
        },
        onError: (errMsg) => {
          setError(errMsg);
          setStatus({ status: 'error', message: errMsg });
        },
        onComplete: () => {
          setStatus(prev => ({ ...prev, status: 'completed', message: '任务完成' }));
        },
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : '执行失败');
      setStatus({ status: 'error', message: '执行失败' });
    } finally {
      setIsRunning(false);
    }
  }, [prompt, isRunning]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSubmit(e as unknown as React.FormEvent);
    }
  }, [handleSubmit]);

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <div className="logo">D</div>
          <h1 className="app-title">DevMate</h1>
        </div>
        <div className="header-right">
          <div className="connection-status">
            <span className={`status-dot ${isConnected ? 'connected' : ''}`} />
            <span>{isConnected ? '已连接' : '未连接'}</span>
          </div>
        </div>
      </header>

      <main className="main-content">
        <div className="left-panel">
          <div className="input-section">
            <form onSubmit={handleSubmit} className="input-wrapper">
              <textarea
                className="prompt-input"
                placeholder="输入你的请求，例如：帮我创建一个待办事项 Web 应用..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={2}
                disabled={isRunning}
              />
              <button
                type="submit"
                className="send-button"
                disabled={!prompt.trim() || isRunning}
              >
                {isRunning ? (
                  <>
                    <span className="loading-spinner" />
                    运行中
                  </>
                ) : (
                  <>
                    <Send size={16} />
                    发送
                  </>
                )}
              </button>
            </form>
          </div>

          {error && (
            <div style={{
              margin: '0 16px 16px',
              padding: '12px',
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid var(--accent-error)',
              borderRadius: 'var(--radius)',
              color: 'var(--accent-error)',
              fontSize: '13px'
            }}>
              {error}
            </div>
          )}

          <AgentFlow
            status={status}
            messages={messages}
            createdFiles={createdFiles}
          />
        </div>

        <div className="right-panel">
          <div className="panel-tabs">
            <button
              className={`panel-tab ${activeTab === 'flow' ? 'active' : ''}`}
              onClick={() => setActiveTab('flow')}
            >
              <Cpu size={14} />
              流程
            </button>
            <button
              className={`panel-tab ${activeTab === 'files' ? 'active' : ''}`}
              onClick={() => setActiveTab('files')}
            >
              <FolderTree size={14} />
              文件
            </button>
          </div>

          <div className="panel-content">
            {activeTab === 'flow' ? (
              <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <h3 style={{ fontSize: '14px', marginBottom: '12px', color: 'var(--text-secondary)' }}>
                  执行摘要
                </h3>
                <div style={{ flex: 1, overflow: 'auto' }}>
                  <div style={{
                    padding: '16px',
                    background: 'var(--bg-tertiary)',
                    borderRadius: 'var(--radius)',
                    marginBottom: '12px'
                  }}>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                      状态
                    </div>
                    <div style={{ fontSize: '14px', fontWeight: 500 }}>
                      {status.status === 'completed' ? '已完成' :
                       status.status === 'error' ? '出错' :
                       status.status === 'idle' ? '等待输入' : '执行中'}
                    </div>
                  </div>
                  <div style={{
                    padding: '16px',
                    background: 'var(--bg-tertiary)',
                    borderRadius: 'var(--radius)',
                    marginBottom: '12px'
                  }}>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                      消息数
                    </div>
                    <div style={{ fontSize: '14px', fontWeight: 500 }}>
                      {messages.length}
                    </div>
                  </div>
                  <div style={{
                    padding: '16px',
                    background: 'var(--bg-tertiary)',
                    borderRadius: 'var(--radius)'
                  }}>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                      生成文件
                    </div>
                    <div style={{ fontSize: '14px', fontWeight: 500 }}>
                      {createdFiles.length} 个
                    </div>
                  </div>

                  {traceUrl && (
                    <div style={{
                      padding: '16px',
                      background: 'rgba(99, 102, 241, 0.1)',
                      border: '1px solid var(--accent-primary)',
                      borderRadius: 'var(--radius)'
                    }}>
                      <div style={{ fontSize: '12px', color: 'var(--accent-primary)', marginBottom: '8px' }}>
                        LangSmith Trace
                      </div>
                      <a
                        href={traceUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          fontSize: '13px',
                          color: 'var(--accent-secondary)',
                          textDecoration: 'none',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          wordBreak: 'break-all'
                        }}
                      >
                        <ExternalLink size={12} />
                        {traceUrl.length > 50 ? traceUrl.slice(0, 50) + '...' : traceUrl}
                      </a>
                    </div>
                  )}

                  {traceShareUrl && (
                    <div style={{
                      padding: '16px',
                      background: 'rgba(34, 197, 94, 0.1)',
                      border: '1px solid #22c55e',
                      borderRadius: 'var(--radius)'
                    }}>
                      <div style={{ fontSize: '12px', color: '#22c55e', marginBottom: '8px' }}>
                        可分享的 Trace 链接
                      </div>
                      <a
                        href={traceShareUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          fontSize: '13px',
                          color: '#22c55e',
                          textDecoration: 'none',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          wordBreak: 'break-all'
                        }}
                      >
                        <ExternalLink size={12} />
                        {traceShareUrl.length > 50 ? traceShareUrl.slice(0, 50) + '...' : traceShareUrl}
                      </a>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <FileManager
                createdFiles={createdFiles}
                onRefresh={() => {}}
              />
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
