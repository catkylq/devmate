import React from 'react';
import { Bot, User, Check, Circle, Loader2 } from 'lucide-react';
import type { AgentMessage, AgentStatus } from '../types';

interface AgentFlowProps {
  status: AgentStatus;
  messages: AgentMessage[];
  createdFiles: string[];
}

const STEPS = [
  { id: 'starting', title: '初始化', description: '启动 Agent 环境' },
  { id: 'thinking', title: '思考', description: '分析用户请求' },
  { id: 'searching', title: '搜索', description: '搜索知识库和网页' },
  { id: 'writing', title: '编写代码', description: '创建和修改文件' },
  { id: 'completed', title: '完成', description: '任务执行完毕' },
];

export const AgentFlow: React.FC<AgentFlowProps> = ({ status, messages, createdFiles }) => {
  const getStepStatus = (stepId: string) => {
    if (status.status === 'completed') {
      return 'completed';
    }
    if (status.status === 'error') {
      return stepId === 'starting' ? 'error' : 'pending';
    }

    const stepOrder = STEPS.map(s => s.id);
    const currentIndex = stepOrder.indexOf(status.status);
    const stepIndex = stepOrder.indexOf(stepId);

    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex) return 'active';
    return 'pending';
  };

  const getStatusText = () => {
    switch (status.status) {
      case 'idle':
        return '等待输入';
      case 'starting':
        return '正在启动...';
      case 'thinking':
        return '正在思考...';
      case 'running':
        return '执行中...';
      case 'completed':
        return '已完成';
      case 'error':
        return '出错了';
      default:
        return status.message;
    }
  };

  const getStatusClass = () => {
    switch (status.status) {
      case 'completed':
        return 'completed';
      case 'error':
        return 'error';
      case 'idle':
        return '';
      default:
        return 'running';
    }
  };

  return (
    <div className="agent-flow">
      <div className="agent-flow-header">
        <h2 className="agent-flow-title">Agent 执行流程</h2>
        <div className={`status-badge ${getStatusClass()}`}>
          {status.status !== 'idle' && status.status !== 'completed' && status.status !== 'error' && (
            <Loader2 size={12} className="loading-spinner" style={{ animation: 'spin 1s linear infinite' }} />
          )}
          {status.status === 'completed' && <Check size={12} />}
          {status.status === 'error' && <Circle size={12} />}
          <span>{getStatusText()}</span>
        </div>
      </div>

      <div className="flow-steps">
        {STEPS.map((step, index) => {
          const stepStatus = getStepStatus(step.id);
          return (
            <div key={step.id} className={`flow-step ${stepStatus}`}>
              <div className="step-indicator">
                {stepStatus === 'completed' ? (
                  <Check size={16} />
                ) : stepStatus === 'active' ? (
                  <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
                ) : (
                  index + 1
                )}
              </div>
              <div className="step-content">
                <div className="step-title">{step.title}</div>
                <div className="step-description">{step.description}</div>
              </div>
            </div>
          );
        })}
      </div>

      {messages.length > 0 && (
        <div className="message-list" style={{ marginTop: '24px' }}>
          <h3 style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '12px' }}>
            对话记录
          </h3>
          {messages.slice(-5).map((msg) => (
            <div key={msg.index} className="message-item">
              <div className="message-header">
                <span className={`message-role ${msg.type}`}>
                  {msg.type === 'user' ? (
                    <>
                      <User size={10} style={{ marginRight: '4px' }} />
                      用户
                    </>
                  ) : (
                    <>
                      <Bot size={10} style={{ marginRight: '4px' }} />
                      Agent
                    </>
                  )}
                </span>
              </div>
              <div className="message-content">
                {msg.content.length > 500 ? msg.content.slice(0, 500) + '...' : msg.content}
              </div>
            </div>
          ))}
        </div>
      )}

      {createdFiles.length > 0 && (
        <div style={{ marginTop: '24px' }}>
          <h3 style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '12px' }}>
            生成的文件
          </h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {createdFiles.map((file) => (
              <span
                key={file}
                style={{
                  padding: '6px 12px',
                  background: 'rgba(16, 185, 129, 0.2)',
                  color: 'var(--accent-success)',
                  borderRadius: '4px',
                  fontSize: '12px',
                  fontFamily: 'monospace',
                }}
              >
                {file}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentFlow;
