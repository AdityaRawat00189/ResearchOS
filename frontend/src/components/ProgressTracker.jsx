import { useState, useEffect, useCallback } from 'react';
import { getStatus } from '../api/client';

const STEPS = [
  { key: 'input_init',      label: 'Input & Queries',    icon: '01' },
  { key: 'web_search',      label: 'Web Search',         icon: '02' },
  { key: 'extraction',      label: 'Content Extraction', icon: '03' },
  { key: 'relevance_check', label: 'Relevance Filter',   icon: '04' },
  { key: 'outline',         label: 'Outline Generation', icon: '05' },
  { key: 'section_writer',  label: 'Section Writing',    icon: '06' },
  { key: 'quality_recheck', label: 'Quality Recheck',    icon: '07' },
  { key: 'validation',      label: 'Validation',         icon: '08' },
  { key: 'export',          label: 'Export & Render',     icon: '09' },
];

const NODE_INDEX = Object.fromEntries(STEPS.map((s, i) => [s.key, i]));

export default function ProgressTracker({ jobId, onComplete }) {
  const [activeIdx, setActiveIdx] = useState(0);
  const [status, setStatus] = useState('running');
  const [errorMsg, setErrorMsg] = useState('');

  const checkStatus = useCallback(async () => {
    try {
      const res = await getStatus(jobId);
      const d = res.data;

      if (d.current_node && NODE_INDEX[d.current_node] !== undefined) {
        setActiveIdx(NODE_INDEX[d.current_node]);
      }

      if (d.status === 'completed') {
        setStatus('completed');
        setActiveIdx(STEPS.length - 1);
        onComplete();
        return true; // stop polling
      }
      if (d.status === 'error' || d.status === 'failed') {
        setStatus('error');
        setErrorMsg(d.error || 'Pipeline encountered an error.');
        return true;
      }
    } catch {
      // network glitch — keep polling
    }
    return false;
  }, [jobId, onComplete]);

  useEffect(() => {
    let timer;
    const poll = async () => {
      const done = await checkStatus();
      if (!done) timer = setTimeout(poll, 3000);
    };
    poll();
    return () => clearTimeout(timer);
  }, [checkStatus]);

  // SVG ring math
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const pct = status === 'completed'
    ? 100
    : Math.round(((activeIdx + 1) / STEPS.length) * 100);
  const dashOffset = circumference - (pct / 100) * circumference;

  return (
    <section className="progress-section animate-in">
      <div className="progress-header">
        <h2 className="progress-title">
          {status === 'completed'
            ? 'Generation Complete'
            : status === 'error'
              ? 'Pipeline Error'
              : 'Generating Your Paper…'}
        </h2>
        <p className="progress-subtitle">
          {status === 'completed'
            ? 'All pipeline stages finished successfully.'
            : status === 'error'
              ? 'Something went wrong during generation.'
              : `Currently on step ${activeIdx + 1} of ${STEPS.length}`}
        </p>
      </div>

      {/* ── Circular progress ──────── */}
      <div className="progress-ring-wrapper">
        <div className="progress-ring-container">
          <svg width="120" height="120" viewBox="0 0 120 120">
            <circle className="progress-ring-bg" cx="60" cy="60" r={radius} />
            <circle
              className="progress-ring-fill"
              cx="60" cy="60" r={radius}
              strokeDasharray={circumference}
              strokeDashoffset={dashOffset}
              style={status === 'error' ? { stroke: 'var(--error)' } : {}}
            />
          </svg>
          <div className="progress-ring-text">
            <span className="progress-ring-pct">{pct}%</span>
            <span className="progress-ring-label">progress</span>
          </div>
        </div>
      </div>

      {/* ── Steps list ─────────────── */}
      <div className="steps-card">
        {STEPS.map((step, i) => {
          const isCompleted = i < activeIdx || status === 'completed';
          const isActive = i === activeIdx && status === 'running';
          const isError = i === activeIdx && status === 'error';

          let indicatorClass = 'step-indicator ';
          if (isCompleted) indicatorClass += 'completed';
          else if (isActive) indicatorClass += 'active';
          else if (isError) indicatorClass += 'error';
          else indicatorClass += 'pending';

          let rowClass = 'step-row';
          if (isCompleted) rowClass += ' is-completed';
          if (isActive) rowClass += ' is-active';

          return (
            <div key={step.key} className={rowClass}>
              <div className={indicatorClass}>
                {isCompleted ? (
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                    <path d="M3 7.5L5.5 10L11 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                ) : isError ? (
                  '!'
                ) : (
                  step.icon
                )}
              </div>
              <span className="step-name">{step.label}</span>
              <span className="step-meta">
                {isCompleted ? 'Done' : isActive ? 'Running' : isError ? 'Failed' : '—'}
              </span>
            </div>
          );
        })}
      </div>

      {status === 'error' && (
        <div className="progress-error-card animate-in">
          <div className="progress-error-title">Error Details</div>
          <div className="progress-error-msg">{errorMsg}</div>
        </div>
      )}
    </section>
  );
}
