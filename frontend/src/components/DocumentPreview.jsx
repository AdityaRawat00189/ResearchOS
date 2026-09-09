import { useState, useEffect } from 'react';
import mammoth from 'mammoth';
import { getPreviewUrl } from '../api/client';

export default function DocumentPreview({ jobId }) {
  const [html, setHtml] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch(getPreviewUrl(jobId));
        if (!res.ok) throw new Error('Failed to fetch document');
        const buf = await res.arrayBuffer();
        const result = await mammoth.convertToHtml({ arrayBuffer: buf });
        setHtml(result.value);
      } catch {
        setError('Could not load the document preview.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [jobId]);

  if (loading) {
    return (
      <div className="preview-card">
        <div className="preview-loading">
          <div className="preview-loading-spinner" />
          Loading document preview…
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="preview-card">
        <div className="preview-loading" style={{ color: 'var(--error)' }}>
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="preview-card">
      <div className="preview-toolbar">
        <div className="preview-toolbar-title">
          <span className="preview-toolbar-dot" />
          Document Preview
        </div>
        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
          Rendered from .docx
        </span>
      </div>
      <div className="preview-body" dangerouslySetInnerHTML={{ __html: html }} />
    </div>
  );
}
