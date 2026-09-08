import { getDownloadUrl } from '../api/client';

export default function DownloadButton({ jobId, enabled }) {
  if (!enabled) return null;

  return (
    <div className="download-container">
      <a 
        href={getDownloadUrl(jobId)} 
        download 
        className="btn-primary btn-large"
        target="_blank" 
        rel="noopener noreferrer"
      >
        Download Paper (.docx)
      </a>
    </div>
  );
}
