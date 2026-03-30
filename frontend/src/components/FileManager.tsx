import React, { useState, useEffect, useCallback } from 'react';
import { 
  FolderOpen, 
  File, 
  Plus, 
  Trash2, 
  Edit3, 
  Save, 
  X,
  RefreshCw,
  FileCode,
  FileText,
  FileJson
} from 'lucide-react';
import Editor from '@monaco-editor/react';
import { api } from '../api';

interface FileManagerProps {
  createdFiles?: string[];
  onRefresh?: () => void;
}

export const FileManager: React.FC<FileManagerProps> = ({ createdFiles = [], onRefresh }) => {
  const [files, setFiles] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [editedContent, setEditedContent] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [showNewModal, setShowNewModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);
  const [newFilePath, setNewFilePath] = useState('');
  const [newFileContent, setNewFileContent] = useState('');
  const [error, setError] = useState<string | null>(null);

  const loadFiles = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.listWorkspace();
      setFiles(data.files);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载文件失败');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadFiles();
  }, [loadFiles]);

  useEffect(() => {
    if (onRefresh) {
      onRefresh();
    }
  }, [createdFiles, onRefresh]);

  const loadFile = async (filePath: string) => {
    setSelectedFile(filePath);
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.readFile(filePath);
      setFileContent(data.content);
      setEditedContent(data.content);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载文件失败');
      setSelectedFile(null);
      setFileContent('');
      setEditedContent('');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!selectedFile) return;
    setIsSaving(true);
    setError(null);
    try {
      await api.updateFile(selectedFile, editedContent);
      setFileContent(editedContent);
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCreate = async () => {
    if (!newFilePath.trim()) return;
    setIsSaving(true);
    setError(null);
    try {
      await api.createFile(newFilePath, newFileContent);
      setShowNewModal(false);
      setNewFilePath('');
      setNewFileContent('');
      await loadFiles();
      loadFile(newFilePath);
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建失败');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (filePath: string) => {
    setIsLoading(true);
    setError(null);
    try {
      await api.deleteFile(filePath);
      setShowDeleteConfirm(null);
      if (selectedFile === filePath) {
        setSelectedFile(null);
        setFileContent('');
        setEditedContent('');
      }
      await loadFiles();
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败');
    } finally {
      setIsLoading(false);
    }
  };

  const getFileIcon = (filePath: string) => {
    const ext = filePath.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'js':
      case 'jsx':
      case 'ts':
      case 'tsx':
      case 'py':
      case 'css':
      case 'html':
        return <FileCode size={14} />;
      case 'json':
      case 'toml':
      case 'yaml':
      case 'yml':
        return <FileJson size={14} />;
      case 'md':
      case 'txt':
        return <FileText size={14} />;
      default:
        return <File size={14} />;
    }
  };

  const getLanguage = (filePath: string) => {
    const ext = filePath.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'js':
        return 'javascript';
      case 'jsx':
        return 'javascript';
      case 'ts':
        return 'typescript';
      case 'tsx':
        return 'typescript';
      case 'py':
        return 'python';
      case 'css':
        return 'css';
      case 'html':
        return 'html';
      case 'json':
        return 'json';
      case 'md':
        return 'markdown';
      case 'toml':
        return 'ini';
      case 'yaml':
      case 'yml':
        return 'yaml';
      default:
        return 'plaintext';
    }
  };

  const isModified = selectedFile && editedContent !== fileContent;
  const isNewFile = (path: string) => createdFiles.includes(path);

  return (
    <div className="file-explorer">
      <div className="file-toolbar">
        <button className="toolbar-button" onClick={loadFiles} disabled={isLoading}>
          <RefreshCw size={14} className={isLoading ? 'loading-spinner' : ''} />
          刷新
        </button>
        <button className="toolbar-button" onClick={() => setShowNewModal(true)}>
          <Plus size={14} />
          新建
        </button>
        {selectedFile && (
          <>
            <button
              className="toolbar-button danger"
              onClick={() => setShowDeleteConfirm(selectedFile)}
            >
              <Trash2 size={14} />
              删除
            </button>
          </>
        )}
      </div>

      {error && (
        <div style={{
          padding: '12px',
          margin: '12px',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid var(--accent-error)',
          borderRadius: 'var(--radius)',
          color: 'var(--accent-error)',
          fontSize: '13px'
        }}>
          {error}
        </div>
      )}

      <div className="file-tree">
        {isLoading && files.length === 0 ? (
          <div className="empty-state">
            <div className="loading-spinner" style={{ width: 24, height: 24 }} />
            <p style={{ marginTop: 12 }}>加载中...</p>
          </div>
        ) : files.length === 0 ? (
          <div className="empty-state">
            <FolderOpen size={48} />
            <p className="empty-state-title">暂无文件</p>
            <p className="empty-state-description">点击"新建"创建第一个文件</p>
          </div>
        ) : (
          files.map((file) => (
            <div
              key={file}
              className={`tree-item ${selectedFile === file ? 'selected' : ''} ${isNewFile(file) ? 'new' : ''}`}
              onClick={() => loadFile(file)}
            >
              {getFileIcon(file)}
              <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {file}
              </span>
              {isNewFile(file) && (
                <span style={{
                  fontSize: '10px',
                  padding: '2px 6px',
                  background: 'var(--accent-success)',
                  color: 'white',
                  borderRadius: '4px'
                }}>
                  新
                </span>
              )}
            </div>
          ))
        )}
      </div>

      {selectedFile && (
        <div className="file-editor">
          <div className="editor-header">
            <span className="file-name">
              {getFileIcon(selectedFile)}
              <span style={{ marginLeft: 8 }}>{selectedFile}</span>
            </span>
            <div className="editor-actions">
              <button
                className={`editor-button ${isModified ? 'save' : ''}`}
                onClick={handleSave}
                disabled={!isModified || isSaving}
              >
                {isSaving ? (
                  <div className="loading-spinner" />
                ) : (
                  <Save size={14} />
                )}
                保存
              </button>
              <button
                className="editor-button"
                onClick={() => {
                  setSelectedFile(null);
                  setFileContent('');
                  setEditedContent('');
                }}
              >
                <X size={14} />
              </button>
            </div>
          </div>
          <div className="editor-container">
            <Editor
              height="100%"
              language={getLanguage(selectedFile)}
              value={editedContent}
              onChange={(value) => setEditedContent(value || '')}
              theme="vs-dark"
              options={{
                minimap: { enabled: false },
                fontSize: 13,
                lineNumbers: 'on',
                scrollBeyondLastLine: false,
                wordWrap: 'on',
                automaticLayout: true,
                padding: { top: 12 },
              }}
            />
          </div>
        </div>
      )}

      {showNewModal && (
        <div className="code-modal-overlay" onClick={() => setShowNewModal(false)}>
          <div className="code-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">新建文件</h3>
              <button className="modal-close" onClick={() => setShowNewModal(false)}>
                <X size={18} />
              </button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">文件路径</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="例如: src/App.tsx"
                  value={newFilePath}
                  onChange={(e) => setNewFilePath(e.target.value)}
                  autoFocus
                />
              </div>
              <div className="form-group">
                <label className="form-label">初始内容 (可选)</label>
                <textarea
                  className="form-textarea"
                  placeholder="输入文件内容..."
                  value={newFileContent}
                  onChange={(e) => setNewFileContent(e.target.value)}
                  rows={6}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowNewModal(false)}>
                取消
              </button>
              <button
                className="btn btn-primary"
                onClick={handleCreate}
                disabled={!newFilePath.trim() || isSaving}
              >
                {isSaving ? <div className="loading-spinner" /> : null}
                创建
              </button>
            </div>
          </div>
        </div>
      )}

      {showDeleteConfirm && (
        <div className="code-modal-overlay" onClick={() => setShowDeleteConfirm(null)}>
          <div className="code-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">确认删除</h3>
              <button className="modal-close" onClick={() => setShowDeleteConfirm(null)}>
                <X size={18} />
              </button>
            </div>
            <div className="modal-body">
              <div className="confirm-dialog">
                <p>确定要删除文件 <strong>{showDeleteConfirm}</strong> 吗？</p>
                <p style={{ color: 'var(--accent-error)', fontSize: '13px' }}>此操作不可撤销</p>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowDeleteConfirm(null)}>
                取消
              </button>
              <button
                className="btn btn-danger"
                onClick={() => handleDelete(showDeleteConfirm)}
                disabled={isLoading}
              >
                {isLoading ? <div className="loading-spinner" /> : null}
                删除
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileManager;
