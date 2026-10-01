import { useState, type FormEvent } from 'react';

interface CreateCampaignProps {
  onSubmit: (name: string) => Promise<void>;
  onCancel: () => void;
}

export function CreateCampaign({ onSubmit, onCancel }: CreateCampaignProps) {
  const [name, setName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) {
      setError('Campaign name cannot be blank.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      await onSubmit(trimmed);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to create campaign');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="create-campaign-container">
      <div className="view-header">
        <div>
          <h2>Create New Campaign</h2>
          <p className="subtitle">Set up a container for images and videos</p>
        </div>
        <button type="button" className="btn btn-secondary" onClick={onCancel} disabled={submitting}>
          Back to Campaigns
        </button>
      </div>

      <div className="card form-card">
        {error && (
          <div className="alert alert-error">
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="campaign-name">Campaign Name</label>
            <input
              id="campaign-name"
              type="text"
              className="form-input"
              placeholder="e.g. AO Gold Colgate SBW"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                if (error) setError(null);
              }}
              disabled={submitting}
              autoFocus
            />
          </div>

          <div className="form-actions">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onCancel}
              disabled={submitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting || !name.trim()}
            >
              {submitting ? 'Creating...' : 'Create Campaign'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
