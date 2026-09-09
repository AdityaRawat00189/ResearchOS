import { useState } from 'react';
import SubmitForm from './components/SubmitForm';
import ProgressTracker from './components/ProgressTracker';
import DocumentPreview from './components/DocumentPreview';
import DownloadButton from './components/DownloadButton';
import './App.css';

function App() {
  const [jobId, setJobId] = useState(null);
  const [view, setView] = useState('form'); // form | processing | completed

  const handleSubmit = (id) => {
    setJobId(id);
    setView('processing');
  };

  const handleComplete = () => {
    setView('completed');
  };

  const handleReset = () => {
    setJobId(null);
    setView('form');
  };

  return (
    <div className="app-shell">
      {/* ── Navbar ─────────────────────── */}
      <nav className="navbar">
        <div className="navbar-brand">
          <div className="navbar-logo">R</div>
          <span className="navbar-title">ResearchOS</span>
          <span className="navbar-tag">Beta</span>
        </div>
        <div className="navbar-links">
          <span
            className={`navbar-link ${view === 'form' ? 'active' : ''}`}
            onClick={handleReset}
          >
            New Paper
          </span>
          {jobId && (
            <span className={`navbar-link ${view === 'processing' ? 'active' : ''}`}>
              Pipeline
            </span>
          )}
        </div>
      </nav>

      {/* ── Views ──────────────────────── */}
      {view === 'form' && (
        <>
          <section className="hero-section animate-in">
            <div className="hero-badge animate-in delay-1">
              <span className="hero-badge-dot" />
              Powered by local Ollama models
            </div>
            <h1 className="hero-title animate-in delay-2">
              Generate publication-ready <em>research papers</em> with AI
            </h1>
            <p className="hero-subtitle animate-in delay-3">
              Enter a topic and let a multi-agent pipeline handle research,
              writing, quality checks, and formatting — all running on your
              local machine.
            </p>
          </section>
          <div className="form-wrapper animate-in delay-4">
            <SubmitForm onSubmitSuccess={handleSubmit} />
          </div>
        </>
      )}

      {view === 'processing' && (
        <ProgressTracker jobId={jobId} onComplete={handleComplete} />
      )}

      {view === 'completed' && (
        <section className="results-section animate-in">
          <div className="results-banner animate-in delay-1">
            <div className="results-banner-left">
              <div className="results-check-icon">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <path d="M5 10.5L8.5 14L15 7" stroke="#2dd4a8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <div>
                <div className="results-banner-title">Paper Generated</div>
                <div className="results-banner-sub">
                  Your research paper is ready to download and review.
                </div>
              </div>
            </div>
            <div className="results-actions">
              <DownloadButton jobId={jobId} />
              <button className="btn btn-secondary" onClick={handleReset}>
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path d="M1 7a6 6 0 1011.2-3M12.2 1v3h-3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                New Paper
              </button>
            </div>
          </div>
          <div className="animate-in delay-2">
            <DocumentPreview jobId={jobId} />
          </div>
        </section>
      )}

      {/* ── Footer ─────────────────────── */}
      <footer className="app-footer">
        <p className="footer-text">
          ResearchOS <span className="accent">v1.0</span> — LangGraph ×
          Ollama multi-agent pipeline
        </p>
      </footer>
    </div>
  );
}

export default App;
