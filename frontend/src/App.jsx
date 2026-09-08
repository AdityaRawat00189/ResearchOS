import { useState } from 'react';
import SubmitForm from './components/SubmitForm';
import ProgressTracker from './components/ProgressTracker';
import DocumentPreview from './components/DocumentPreview';
import DownloadButton from './components/DownloadButton';
import './App.css';

function App() {
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState('form');

  const handleFormSubmit = (id) => {
    setJobId(id);
    setStatus('processing');
  };

  const handleProcessComplete = () => {
    setStatus('completed');
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>ResearchOS — AI Research Paper Generator</h1>
      </header>
      
      <main className="app-main">
        {status === 'form' && (
          <SubmitForm onSubmitSuccess={handleFormSubmit} />
        )}
        
        {status === 'processing' && (
          <ProgressTracker jobId={jobId} onComplete={handleProcessComplete} />
        )}
        
        {status === 'completed' && (
          <div className="results-view">
            <div className="results-header">
              <h2>Paper Generated Successfully!</h2>
              <DownloadButton jobId={jobId} enabled={true} />
            </div>
            <DocumentPreview jobId={jobId} />
            <button 
              className="btn-secondary mt-4" 
              onClick={() => {
                setJobId(null);
                setStatus('form');
              }}
            >
              Start New Paper
            </button>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
