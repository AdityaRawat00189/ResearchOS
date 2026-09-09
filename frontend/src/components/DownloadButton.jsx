import { getDownloadUrl } from '../api/client';

export default function DownloadButton({ jobId }) {
  return (
    <a
      href={getDownloadUrl(jobId)}
      download
      className="btn-download"
      target="_blank"
      rel="noopener noreferrer"
    >
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <path d="M2 11v2a1 1 0 001 1h10a1 1 0 001-1v-2M8 2v9M5 8l3 3 3-3"
          stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
      Download .docx
    </a>
  );
}
