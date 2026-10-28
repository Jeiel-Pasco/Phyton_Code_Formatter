import React, { useState, useEffect, useRef } from 'react';
import './styles.css';

const LANGUAGE = 'python';          // project scope: Python only
const FILE_EXT = '.py';
const INDENT_SIZE = 4;              // fixed style rule
const SAMPLE_CODE = `# greet the user\nx=10\nname="Ana"\nif x>5:\n  print("big "+name)\nelse:\n        print("small")\nwhile x>0:\n x=x-1`;

export default function App() {
  const [code, setCode] = useState(SAMPLE_CODE);
  const [formattedCode, setFormattedCode] = useState('');
  const [indentStyle, setIndentStyle] = useState('spaces');
  const [maxLineLength, setMaxLineLength] = useState(80);
  const [theme, setTheme] = useState('dark');
  const [isFormatting, setIsFormatting] = useState(false);
  const [errorInfo, setErrorInfo] = useState(null);
  const [metrics, setMetrics] = useState({
    commentsPreserved: 1,
    executionTimeMs: 0.18,
    originalLines: 6,
    formattedLines: 15,
    lexerStatus: 'OK',
    parserStatus: 'OK'
  });
  const [toastMessage, setToastMessage] = useState('');

  const inputGutterRef = useRef(null);
  const outputGutterRef = useRef(null);
  const inputTextareaRef = useRef(null);
  const outputPreRef = useRef(null);

  // Sync theme attribute on <html> element
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  // Initial format on load
  useEffect(() => {
    handleFormat(SAMPLE_CODE);
  }, []);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(''), 2500);
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        handleFormat();
      } else if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        handleClear();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [code, indentStyle, maxLineLength]);

  const handleFormat = async (
    targetCode = code,
    targetStyle = indentStyle,
    targetLineLength = maxLineLength
  ) => {
    setIsFormatting(true);
    setErrorInfo(null);

    try {
      const response = await fetch('/api/format', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code: targetCode,
          language: LANGUAGE,
          indent_size: INDENT_SIZE,
          indent_style: targetStyle,
          max_line_length: targetLineLength
        })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setFormattedCode(data.formatted_code);
        setMetrics({
          commentsPreserved: data.comments_preserved ?? 0,
          executionTimeMs: data.execution_time_ms ?? 0,
          originalLines: data.original_lines ?? 0,
          formattedLines: data.formatted_lines ?? 0,
          lexerStatus: data.lexer_status || 'OK',
          parserStatus: data.parser_status || 'OK'
        });
        setErrorInfo(null);
      } else {
        setErrorInfo({
          type: data.error?.type || 'Syntax error',
          message: data.user_message || data.error?.message || 'Error occurred while formatting code.',
          line: data.error?.line,
          column: data.error?.column,
          suggestion: data.error?.suggestion || 'Fix the source and format again.'
        });
      }
    } catch (err) {
      console.warn('Backend API connection error:', err);
      setErrorInfo({
        type: 'Connection error',
        message: 'Could not connect to Flask API backend (port 5000). Ensure the backend server is running.',
        suggestion: 'Run "python backend/app.py" to start the Flask service.'
      });
    } finally {
      setIsFormatting(false);
    }
  };

  const handleClear = () => {
    setCode('');
    setFormattedCode('');
    setErrorInfo(null);
    showToast('Editor cleared');
  };

  const handleCopy = async () => {
    if (!formattedCode) {
      showToast('No formatted code to copy');
      return;
    }
    try {
      await navigator.clipboard.writeText(formattedCode);
      showToast('Copied to clipboard!');
    } catch {
      showToast('Failed to copy');
    }
  };

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      setCode(text);
      handleFormat(text);
      showToast('Pasted and formatted!');
    } catch {
      showToast('Clipboard access denied');
    }
  };

  const handleDownload = () => {
    const ext = FILE_EXT;
    const filename = `formatted_code${ext}`;
    const blob = new Blob([formattedCode || code], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
    showToast(`Downloaded ${filename}`);
  };

  // Support Tab key indentation inside textarea
  const handleKeyDownInTextarea = (e) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const textarea = e.target;
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const spaces = ' '.repeat(INDENT_SIZE);
      const newCode = code.substring(0, start) + spaces + code.substring(end);
      setCode(newCode);
      setTimeout(() => {
        textarea.selectionStart = textarea.selectionEnd = start + INDENT_SIZE;
      }, 0);
    }
  };

  // Line numbers calculation
  const inputLineCount = Math.max(code.split('\n').length, 1);
  const outputLineCount = Math.max(formattedCode ? formattedCode.split('\n').length : 1, 1);

  const syncInputScroll = (e) => {
    if (inputGutterRef.current) {
      inputGutterRef.current.scrollTop = e.target.scrollTop;
    }
  };

  const syncOutputScroll = (e) => {
    if (outputGutterRef.current) {
      outputGutterRef.current.scrollTop = e.target.scrollTop;
    }
  };

  return (
    <div className="app-container">
      {/* Header Bar */}
      <header className="app-header">
        <div className="header-brand">
          <div className="brand-row">
            <svg className="brand-logo-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="16 18 22 12 16 6"></polyline>
              <polyline points="8 6 2 12 8 18"></polyline>
            </svg>
            <h1 className="brand-title">MiniLang Formatter</h1>
          </div>
          <p className="brand-subtitle">Paste messy code. Get consistent code. Comments stay.</p>
        </div>

        <div className="header-controls">
          {/* Format Button (Highlighted Amber) */}
          <button
            className="btn btn-format"
            onClick={() => handleFormat()}
            disabled={isFormatting}
            title="Format Code (Ctrl + Enter)"
          >
            {isFormatting ? 'Formatting...' : 'Format'}
          </button>

          {/* Download Button */}
          <button
            className="btn btn-secondary"
            onClick={handleDownload}
            title={`Download formatted code as ${FILE_EXT}`}
          >
            Download {FILE_EXT}
          </button>

          {/* Theme Toggle */}
          <button
            className="btn btn-secondary btn-icon"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            title="Toggle Light/Dark Theme"
          >
            {theme === 'dark' ? (
              <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="5" strokeWidth="2"/>
                <path strokeWidth="2" strokeLinecap="round" d="M12 1v2m0 18v2M4.22 4.22l1.42 1.42m12.72 12.72l1.42 1.42M1 12h2m18 0h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
              </svg>
            ) : (
              <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/>
              </svg>
            )}
          </button>
        </div>
      </header>

      {/* Editor Section: Desktop Side-by-Side */}
      <main className="editor-workspace">
        {/* Left Panel: SOURCE (MESSY) */}
        <section className="editor-card">
          <div className="editor-header">
            <span className="editor-title">SOURCE (MESSY)</span>
            <div className="editor-actions">
              <button className="btn-action" onClick={handlePaste} title="Paste code from clipboard">
                Paste
              </button>
              <button className="btn-action" onClick={handleClear} title="Clear source code (Ctrl + K)">
                Clear
              </button>
            </div>
          </div>
          <div className="editor-body">
            <div className="line-numbers" ref={inputGutterRef}>
              {Array.from({ length: inputLineCount }, (_, i) => (
                <div key={i + 1} className="line-number-item">{i + 1}</div>
              ))}
            </div>
            <textarea
              ref={inputTextareaRef}
              className="code-textarea"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              onKeyDown={handleKeyDownInTextarea}
              onScroll={syncInputScroll}
              placeholder="Paste or type unformatted code here..."
              spellCheck="false"
              autoCapitalize="off"
              autoComplete="off"
            />
          </div>
        </section>

        {/* Right Panel: FORMATTED OUTPUT */}
        <section className="editor-card output-card">
          <div className="editor-header">
            <span className="editor-title">FORMATTED OUTPUT</span>
            <div className="editor-actions">
              <button className="btn-action" onClick={handleCopy} title="Copy formatted code to clipboard">
                Copy
              </button>
              <button className="btn-action" onClick={handleDownload} title="Download file">
                Save
              </button>
            </div>
          </div>
          <div className="editor-body">
            <div className="line-numbers" ref={outputGutterRef}>
              {Array.from({ length: outputLineCount }, (_, i) => (
                <div key={i + 1} className="line-number-item">{i + 1}</div>
              ))}
            </div>
            <pre
              ref={outputPreRef}
              className="code-display"
              onScroll={syncOutputScroll}
            >
              <code>{formattedCode || '// Click "Format" or press Ctrl+Enter to format code'}</code>
            </pre>
          </div>
        </section>
      </main>

      {/* Bottom Pipeline Status Bar */}
      <footer className="status-bar">
        <span className="status-badge-success">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
          Formatted successfully
        </span>
        <span className="status-separator">•</span>
        <span className="status-item">Lexer: <strong>{metrics.lexerStatus}</strong></span>
        <span className="status-separator">•</span>
        <span className="status-item">Parser: <strong>{metrics.parserStatus}</strong></span>
        <span className="status-separator">•</span>
        <span className="status-item">Comments preserved: <strong>{metrics.commentsPreserved}</strong></span>
        <span className="status-separator">•</span>
        <span className="status-item">Indent: <strong>{INDENT_SIZE} {indentStyle}</strong></span>
        <span className="status-separator">•</span>
        <span className="status-item">Max line: <strong>{maxLineLength}</strong></span>
        <span className="status-separator">•</span>
        <span className="status-item">Time: <strong>{metrics.executionTimeMs}ms</strong></span>
        <span className="status-separator">•</span>
        <span className="status-item">Lines: <strong>{metrics.originalLines} → {metrics.formattedLines}</strong></span>
      </footer>

      {/* Error State Banner (Replicating Mockup) */}
      {errorInfo && (
        <div className="error-banner">
          <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
          </svg>
          <div>
            <strong>{errorInfo.type}:</strong> {errorInfo.message}{' '}
            {errorInfo.suggestion && <code>{errorInfo.suggestion}</code>}
          </div>
        </div>
      )}

      {/* Toast Notification */}
      {toastMessage && (
        <div className="toast">
          {toastMessage}
        </div>
      )}
    </div>
  );
}
