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
      setError('Topic is required');
      return;
    }
    setError('');
    setLoading(true);
    
    try {
      const payload = {
        topic,
        min_pages: minPages,
        citation_style: citationStyle,
        keywords: keywords.split(',').map(k => k.trim()).filter(Boolean),
        domain
      };
      const response = await generatePaper(payload);
      onSubmitSuccess(response.data.job_id || response.data.jobId);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to submit request');
      setLoading(false);
    }
  };

  return (
    <div className="card form-container">
      <h2>Generate New Paper</h2>
      {error && <div className="error-message">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Topic *</label>
          <input 
            type="text" 
            value={topic} 
            onChange={(e) => setTopic(e.target.value)} 
            placeholder="Enter research topic"
            required
          />
        </div>
        
        <div className="form-row">
          <div className="form-group">
            <label>Min Pages</label>
            <input 
              type="number" 
              value={minPages} 
              onChange={(e) => setMinPages(parseInt(e.target.value))} 
              min="1"
            />
          </div>
          
          <div className="form-group">
            <label>Citation Style</label>
            <select value={citationStyle} onChange={(e) => setCitationStyle(e.target.value)}>
              <option value="APA">APA</option>
              <option value="IEEE">IEEE</option>
            </select>
          </div>
        </div>

        <div className="form-group">
          <label>Keywords (comma-separated)</label>
          <input 
            type="text" 
            value={keywords} 
            onChange={(e) => setKeywords(e.target.value)} 
            placeholder="e.g. machine learning, neural networks"
          />
        </div>

        <div className="form-group">
          <label>Domain (optional)</label>
          <input 
            type="text" 
            value={domain} 
            onChange={(e) => setDomain(e.target.value)} 
            placeholder="e.g. Computer Science"
          />
        </div>

        <button type="submit" disabled={loading} className="btn-primary">
          {loading ? 'Submitting...' : 'Generate Paper'}
        </button>
      </form>
    </div>
  );
}
