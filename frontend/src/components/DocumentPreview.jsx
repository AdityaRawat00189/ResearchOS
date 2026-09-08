import { useState, useEffect } from 'react';
import mammoth from 'mammoth';
import { getPreviewUrl } from '../api/client';

export default function DocumentPreview({ jobId }) {
  const [htmlContent, setHtmlContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDocx = async () => {
      try {
        const response = await fetch(getPreviewUrl(jobId));
        if (!response.ok) throw new Error('Failed to fetch document');
        
        const arrayBuffer = await response.arrayBuffer();
        const result = await mammoth.convertToHtml({ arrayBuffer });
        setHtmlContent(result.value);
        setLoading(false);
      } catch (err) {
        setError('Could not load document preview.');
        setLoading(false);
      }
    };

    fetchDocx();
  }, [jobId]);

  if (loading) return <div className="preview-loading">Loading preview...</div>;
  if (error) return <div className="error-message">{error}</div>;

  return (
    <div className="card preview-container">
      <h2>Document Preview</h2>
      <div className="paper-preview">
        <div dangerouslySetInnerHTML={{ __html: htmlContent }} />
      </div>
    </div>
  );
}
