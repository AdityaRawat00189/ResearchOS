import { useState } from 'react';
import { generatePaper } from '../api/client';

export default function SubmitForm({ onSubmitSuccess }) {
  const [topic, setTopic] = useState('');
  const [minPages, setMinPages] = useState(5);
  const [citationStyle, setCitationStyle] = useState('APA');
  const [keywords, setKeywords] = useState('');
  const [domain, setDomain] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!topic.trim()) {
      setError('Please enter a research topic.');
      return;
    }
    setError('');
    setLoading(true);

    try {
      const payload = {
        topic: topic.trim(),
        min_pages: minPages,
        citation_style: citationStyle,
        keywords: keywords ? keywords.split(',').map(k => k.trim()).filter(Boolean) : [],
        domain: domain.trim(),
      };
      const res = await generatePaper(payload);
      onSubmitSuccess(res.data.job_id || res.data.jobId);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Something went wrong.');
      setLoading(false);
    }
  };

  return (
    <div className="form-card">
      <div className="form-header">
        <div className="form-label-main">Configure Your Paper</div>
        <div className="form-label-sub">Fill in the details and hit generate.</div>
      </div>

      {error && (
        <div className="alert-error">
          <span className="alert-icon">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.5"/>
              <path d="M8 5v3.5M8 10.5h.007" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
          </span>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="field">
          <label className="field-label">
            Research Topic <span className="required">*</span>
          </label>
          <input
            className="field-input"
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g. Impact of AI on Higher Education"
          />
        </div>

        <div className="field-row">
          <div className="field">
            <label className="field-label">Minimum Pages</label>
            <input
              className="field-input"
              type="number"
              value={minPages}
              onChange={(e) => setMinPages(parseInt(e.target.value) || 1)}
              min="1"
              max="30"
            />
          </div>
          <div className="field">
            <label className="field-label">Citation Style</label>
            <select
              className="field-input field-select"
              value={citationStyle}
              onChange={(e) => setCitationStyle(e.target.value)}
            >
              <option value="APA">APA</option>
              <option value="IEEE">IEEE</option>
            </select>
          </div>
        </div>

        <div className="field">
          <label className="field-label">Keywords</label>
          <input
            className="field-input"
            type="text"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            placeholder="machine learning, neural networks, NLP"
          />
          <div className="field-hint">Separate with commas</div>
        </div>

        <div className="field">
          <label className="field-label">Domain</label>
          <input
            className="field-input"
            type="text"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            placeholder="Computer Science"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="btn btn-primary btn-lg btn-full"
        >
          {loading ? (
            <>
              <span className="btn-spinner" />
              Submitting…
            </>
          ) : (
            <>
              Generate Paper
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </>
          )}
        </button>
      </form>
    </div>
  );
}
