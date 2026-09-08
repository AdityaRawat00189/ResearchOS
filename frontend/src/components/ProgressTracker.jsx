import { useState, useEffect } from 'react';
import { getStatus } from '../api/client';

const STEPS = [
  'Input/Init',
  'Web Search',
  'Extraction',
  'Relevance Check',
  'Outline',
  'Section Writing',
  'Quality Recheck',
  'Validation',
  'Export'
];

export default function ProgressTracker({ jobId, onComplete }) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [status, setStatus] = useState('processing');
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    let interval;
    
    const NODE_MAP = {
      'input_init': 0,
      'web_search': 1,
      'extraction': 2,
      'relevance_check': 3,
      'outline': 4,
      'section_writer': 5,
      'quality_recheck': 6,
      'validation': 7,
      'export': 8,
    };

    const checkStatus = async () => {
      try {
        const response = await getStatus(jobId);
        const data = response.data;
        
        if (data.current_node && NODE_MAP[data.current_node] !== undefined) {
          setCurrentStepIndex(NODE_MAP[data.current_node]);
        }

        if (data.status === 'completed') {
          setStatus('completed');
          setCurrentStepIndex(STEPS.length - 1);
          clearInterval(interval);
          onComplete();
        } else if (data.status === 'error' || data.status === 'failed') {
          setStatus('error');
          setErrorMsg(data.error || 'An error occurred during generation');
          clearInterval(interval);
        }
      } catch (err) {
        console.error("Status check failed", err);
      }
    };

    checkStatus();
    interval = setInterval(checkStatus, 3000);

    return () => clearInterval(interval);
  }, [jobId, onComplete]);

  const progressPercentage = Math.round(((currentStepIndex + 1) / STEPS.length) * 100);

  return (
    <div className="card progress-container">
      <h2>Generation Progress</h2>
      <div className="progress-bar-container">
        <div 
          className={`progress-bar ${status === 'error' ? 'error' : ''}`}
          style={{ width: `${progressPercentage}%` }}
        ></div>
      </div>
      <p className="progress-text">{progressPercentage}% Complete</p>
      
      {status === 'error' && (
        <div className="error-message">
          <strong>Error:</strong> {errorMsg}
        </div>
      )}
      
      <ul className="steps-list">
        {STEPS.map((step, index) => {
          let className = "step-item ";
          if (index < currentStepIndex || status === 'completed') className += "completed";
          else if (index === currentStepIndex && status !== 'error') className += "current";
          else if (index === currentStepIndex && status === 'error') className += "error-step";

          return (
            <li key={step} className={className}>
              <span className="step-icon">
                {index < currentStepIndex || status === 'completed' ? '✓' : index + 1}
              </span>
              <span className="step-label">{step}</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
