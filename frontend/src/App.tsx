import { useEffect, useState } from 'react';
import { checkHealth } from './services/api';
import './App.css';

export default function App() {
  const [backendStatus, setBackendStatus] = useState<string>('checking...');
  const [isError, setIsError] = useState<boolean>(false);

  useEffect(() => {
    checkHealth()
      .then((data) => {
        setBackendStatus(data.status);
        setIsError(false);
      })
      .catch(() => {
        setBackendStatus('unreachable (backend offline or loading)');
        setIsError(true);
      });
  }, []);

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>CreativeLens</h1>
        <p className="subtitle">Marketing Creative Evaluation Platform</p>
      </header>

      <main className="main-content">
        <div className="status-card">
          <h2>Application Status</h2>
          <div className="status-row">
            <span className="label">Frontend:</span>
            <span className="badge badge-success">Running</span>
          </div>
          <div className="status-row">
            <span className="label">Backend Status:</span>
            <span className={`badge ${isError ? 'badge-warning' : 'badge-success'}`}>
              {backendStatus}
            </span>
          </div>
          <p className="description">
            Local-first platform for campaign management, creative asset processing, and multi-model evaluation.
          </p>
        </div>
      </main>
    </div>
  );
}
