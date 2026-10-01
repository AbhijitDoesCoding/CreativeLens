import { useState } from 'react';
import type { CreateModelInput, Model, UpdateModelInput } from '../types';

interface ModelManagementProps {
  models: Model[];
  loading: boolean;
  onRefresh: () => Promise<void>;
  onCreateModel: (data: CreateModelInput) => Promise<void>;
  onUpdateModel: (modelId: string, data: UpdateModelInput) => Promise<void>;
  onEnableModel: (modelId: string) => Promise<void>;
  onDisableModel: (modelId: string) => Promise<void>;
}

export function ModelManagement({
  models,
  loading,
  onCreateModel,
  onUpdateModel,
  onEnableModel,
  onDisableModel,
}: ModelManagementProps) {
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [editingModel, setEditingModel] = useState<Model | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  // Form states for creation
  const [name, setName] = useState<string>('');
  const [provider, setProvider] = useState<string>('mock');
  const [modelKey, setModelKey] = useState<string>('mock-vision-v1');
  const [modelType, setModelType] = useState<string>('multimodal');
  const [enabled, setEnabled] = useState<boolean>(true);
  const [configJsonStr, setConfigJsonStr] = useState<string>('{\n  "temperature": 0.2,\n  "max_tokens": 1024\n}');
  const [pricingJsonStr, setPricingJsonStr] = useState<string>('{\n  "input_per_million": 0.15,\n  "output_per_million": 0.60\n}');

  // Form states for editing
  const [editName, setEditName] = useState<string>('');
  const [editConfigJsonStr, setEditConfigJsonStr] = useState<string>('');
  const [editPricingJsonStr, setEditPricingJsonStr] = useState<string>('');

  const enabledCount = models.filter((m) => m.enabled).length;

  const handleOpenEdit = (model: Model) => {
    setEditingModel(model);
    setEditName(model.name);
    setEditConfigJsonStr(
      model.configuration_json ? JSON.stringify(model.configuration_json, null, 2) : ''
    );
    setEditPricingJsonStr(
      model.pricing_json ? JSON.stringify(model.pricing_json, null, 2) : ''
    );
    setFormError(null);
  };

  const handleToggle = async (model: Model) => {
    try {
      setActionLoading(model.id);
      if (model.enabled) {
        await onDisableModel(model.id);
      } else {
        await onEnableModel(model.id);
      }
    } finally {
      setActionLoading(null);
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    let parsedConfig: Record<string, any> | null = null;
    let parsedPricing: Record<string, any> | null = null;

    if (configJsonStr.trim()) {
      try {
        parsedConfig = JSON.parse(configJsonStr);
      } catch {
        setFormError('Invalid JSON in Configuration field.');
        return;
      }
    }

    if (pricingJsonStr.trim()) {
      try {
        parsedPricing = JSON.parse(pricingJsonStr);
      } catch {
        setFormError('Invalid JSON in Pricing field.');
        return;
      }
    }

    try {
      setActionLoading('create');
      await onCreateModel({
        name: name.trim(),
        provider: provider.trim(),
        model_key: modelKey.trim(),
        model_type: modelType.trim() || 'multimodal',
        enabled,
        configuration_json: parsedConfig,
        pricing_json: parsedPricing,
      });

      // Reset and close
      setShowCreateModal(false);
      setName('');
      setProvider('mock');
      setModelKey('mock-vision-v1');
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFormError(err.message);
      } else {
        setFormError('Failed to register model.');
      }
    } finally {
      setActionLoading(null);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingModel) return;
    setFormError(null);

    let parsedConfig: Record<string, any> | null = null;
    let parsedPricing: Record<string, any> | null = null;

    if (editConfigJsonStr.trim()) {
      try {
        parsedConfig = JSON.parse(editConfigJsonStr);
      } catch {
        setFormError('Invalid JSON in Configuration field.');
        return;
      }
    }

    if (editPricingJsonStr.trim()) {
      try {
        parsedPricing = JSON.parse(editPricingJsonStr);
      } catch {
        setFormError('Invalid JSON in Pricing field.');
        return;
      }
    }

    try {
      setActionLoading(editingModel.id);
      await onUpdateModel(editingModel.id, {
        name: editName.trim(),
        configuration_json: parsedConfig,
        pricing_json: parsedPricing,
      });
      setEditingModel(null);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFormError(err.message);
      } else {
        setFormError('Failed to update model.');
      }
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="model-management-container">
      <div className="view-header">
        <div>
          <h2>Model Registry</h2>
          <p className="subtitle">
            Configure multimodal AI vision models. Only enabled models are eligible for inference.
          </p>
        </div>

        <div className="header-actions">
          <div className="model-stats-pill">
            <span>
              Enabled: <strong>{enabledCount}</strong> / {models.length}
            </span>
          </div>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => {
              setFormError(null);
              setShowCreateModal(true);
            }}
          >
            + Register Model
          </button>
        </div>
      </div>

      {loading ? (
        <div className="card loading-card">
          <div className="spinner"></div>
          <p>Loading registered models...</p>
        </div>
      ) : models.length === 0 ? (
        <div className="card empty-card">
          <p className="empty-title">No models registered yet</p>
          <p className="empty-subtitle">
            Register your first vision model (e.g. Mock Model, Gemini Flash, GPT-4o) to begin.
          </p>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => setShowCreateModal(true)}
          >
            Register First Model
          </button>
        </div>
      ) : (
        <div className="assets-table-container card">
          <table className="assets-table">
            <thead>
              <tr>
                <th>Model Name</th>
                <th>Provider</th>
                <th>Model Key</th>
                <th>Type</th>
                <th>Status</th>
                <th>Configuration</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {models.map((model) => {
                const isBusy = actionLoading === model.id;
                return (
                  <tr key={model.id}>
                    <td>
                      <strong>{model.name}</strong>
                    </td>
                    <td>
                      <span className="badge badge-neutral">{model.provider}</span>
                    </td>
                    <td>
                      <code className="meta-pill">{model.model_key}</code>
                    </td>
                    <td>
                      <span className="text-muted" style={{ fontSize: '0.85rem' }}>
                        {model.model_type}
                      </span>
                    </td>
                    <td>
                      <span
                        className={`badge badge-status ${
                          model.enabled ? 'badge-completed' : 'badge-pending'
                        }`}
                      >
                        {model.enabled ? '● Enabled' : '○ Disabled'}
                      </span>
                    </td>
                    <td>
                      <div className="table-meta">
                        {model.configuration_json ? (
                          <span>
                            Config: {Object.keys(model.configuration_json).length} keys
                          </span>
                        ) : (
                          <span className="text-muted">Default config</span>
                        )}
                        {model.pricing_json && (
                          <span className="text-muted" style={{ fontSize: '0.72rem' }}>
                            Pricing configured
                          </span>
                        )}
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                        <button
                          type="button"
                          className={`btn btn-sm ${model.enabled ? 'btn-secondary' : 'btn-primary'}`}
                          onClick={() => handleToggle(model)}
                          disabled={isBusy}
                        >
                          {isBusy ? '...' : model.enabled ? 'Disable' : 'Enable'}
                        </button>
                        <button
                          type="button"
                          className="btn btn-sm btn-secondary"
                          onClick={() => handleOpenEdit(model)}
                          disabled={isBusy}
                        >
                          Configure
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Register Model Modal */}
      {showCreateModal && (
        <div className="modal-backdrop" onClick={() => setShowCreateModal(false)}>
          <div
            className="modal-content form-modal"
            onClick={(e) => e.stopPropagation()}
            style={{ maxWidth: '600px' }}
          >
            <div className="modal-header">
              <h3>Register New Model</h3>
              <button
                type="button"
                className="modal-close"
                onClick={() => setShowCreateModal(false)}
              >
                &times;
              </button>
            </div>
            <form onSubmit={handleCreateSubmit}>
              <div style={{ padding: '1.25rem 1.5rem', maxHeight: '70vh', overflowY: 'auto' }}>
                {formError && (
                  <div className="alert alert-error" style={{ marginBottom: '1rem' }}>
                    <span>{formError}</span>
                  </div>
                )}

                <div className="form-group">
                  <label htmlFor="model-name">Model Display Name *</label>
                  <input
                    id="model-name"
                    type="text"
                    className="form-input"
                    placeholder="e.g. Mock Vision Model v1"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div className="form-group">
                    <label htmlFor="model-provider">Provider *</label>
                    <input
                      id="model-provider"
                      type="text"
                      className="form-input"
                      placeholder="e.g. mock, google, openai"
                      value={provider}
                      onChange={(e) => setProvider(e.target.value)}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="model-key">Model Key *</label>
                    <input
                      id="model-key"
                      type="text"
                      className="form-input"
                      placeholder="e.g. mock-vision-v1, gemini-1.5-flash"
                      value={modelKey}
                      onChange={(e) => setModelKey(e.target.value)}
                      required
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="model-type">Model Type</label>
                  <input
                    id="model-type"
                    type="text"
                    className="form-input"
                    value={modelType}
                    onChange={(e) => setModelType(e.target.value)}
                  />
                </div>

                <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <input
                    id="model-enabled"
                    type="checkbox"
                    checked={enabled}
                    onChange={(e) => setEnabled(e.target.checked)}
                    style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                  />
                  <label htmlFor="model-enabled" style={{ margin: 0, cursor: 'pointer' }}>
                    Enable this model immediately for pipeline execution
                  </label>
                </div>

                <div className="form-group">
                  <label htmlFor="config-json">Configuration JSON (Optional)</label>
                  <textarea
                    id="config-json"
                    className="form-input"
                    rows={4}
                    value={configJsonStr}
                    onChange={(e) => setConfigJsonStr(e.target.value)}
                    style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}
                  />
                  <small className="text-muted" style={{ display: 'block', marginTop: '0.25rem' }}>
                    Note: Do NOT store sensitive API keys in the database. Use server environment variables for credentials.
                  </small>
                </div>

                <div className="form-group">
                  <label htmlFor="pricing-json">Pricing JSON (Optional)</label>
                  <textarea
                    id="pricing-json"
                    className="form-input"
                    rows={3}
                    value={pricingJsonStr}
                    onChange={(e) => setPricingJsonStr(e.target.value)}
                    style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}
                  />
                </div>
              </div>

              <div className="form-actions" style={{ padding: '1rem 1.5rem', borderTop: '1px solid #e5e7eb' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={actionLoading === 'create'}
                >
                  {actionLoading === 'create' ? 'Registering...' : 'Register Model'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Configuration Modal */}
      {editingModel && (
        <div className="modal-backdrop" onClick={() => setEditingModel(null)}>
          <div
            className="modal-content form-modal"
            onClick={(e) => e.stopPropagation()}
            style={{ maxWidth: '600px' }}
          >
            <div className="modal-header">
              <h3>Configure {editingModel.name}</h3>
              <button
                type="button"
                className="modal-close"
                onClick={() => setEditingModel(null)}
              >
                &times;
              </button>
            </div>
            <form onSubmit={handleEditSubmit}>
              <div style={{ padding: '1.25rem 1.5rem', maxHeight: '70vh', overflowY: 'auto' }}>
                {formError && (
                  <div className="alert alert-error" style={{ marginBottom: '1rem' }}>
                    <span>{formError}</span>
                  </div>
                )}

                <div className="form-group">
                  <label htmlFor="edit-name">Model Name</label>
                  <input
                    id="edit-name"
                    type="text"
                    className="form-input"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="edit-config">Configuration JSON</label>
                  <textarea
                    id="edit-config"
                    className="form-input"
                    rows={5}
                    value={editConfigJsonStr}
                    onChange={(e) => setEditConfigJsonStr(e.target.value)}
                    style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="edit-pricing">Pricing JSON</label>
                  <textarea
                    id="edit-pricing"
                    className="form-input"
                    rows={4}
                    value={editPricingJsonStr}
                    onChange={(e) => setEditPricingJsonStr(e.target.value)}
                    style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}
                  />
                </div>
              </div>

              <div className="form-actions" style={{ padding: '1rem 1.5rem', borderTop: '1px solid #e5e7eb' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setEditingModel(null)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={actionLoading === editingModel.id}
                >
                  {actionLoading === editingModel.id ? 'Saving...' : 'Save Configuration'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
