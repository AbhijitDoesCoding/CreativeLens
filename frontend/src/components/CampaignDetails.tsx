import { useEffect, useRef, useState, type ChangeEvent } from 'react';
import type {
  Asset,
  Campaign,
  CampaignRunSummary,
  FrameInfo,
  InferenceRun,
  MediaProcessing,
  Model,
} from '../types';
import {
  getAssetFileUrl,
  getAssetFrames,
  getAssetInferenceRuns,
  getAssetProcessing,
  getFrameUrl,
  getModels,
  inferAsset,
  processAsset,
  runCampaignPipeline,
} from '../services/api';

interface CampaignDetailsProps {
  campaign: Campaign;
  assets: Asset[];
  loading: boolean;
  onBack: () => void;
  onUploadFiles: (files: File[]) => Promise<void>;
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatDuration(durationMs?: number | null): string {
  if (!durationMs) return '0s';
  const sec = (durationMs / 1000).toFixed(1);
  return `${sec}s`;
}

export function CampaignDetails({
  campaign,
  assets,
  loading,
  onBack,
  onUploadFiles,
}: CampaignDetailsProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');
  const [previewModalItem, setPreviewModalItem] = useState<{
    title: string;
    mediaType: 'image' | 'video';
    url: string;
    details?: string;
  } | null>(null);

  // Media Processing states
  const [processingMap, setProcessingMap] = useState<Record<string, MediaProcessing>>({});
  const [processingLoading, setProcessingLoading] = useState<Record<string, boolean>>({});
  const [videoFramesMap, setVideoFramesMap] = useState<Record<string, FrameInfo[]>>({});
  const [expandedGallery, setExpandedGallery] = useState<Record<string, boolean>>({});

  // Models & Inference states
  const [enabledModels, setEnabledModels] = useState<Model[]>([]);
  const [inferenceRunsMap, setInferenceRunsMap] = useState<Record<string, InferenceRun[]>>({});
  const [inferringMap, setInferringMap] = useState<Record<string, boolean>>({});
  const [pipelineRunning, setPipelineRunning] = useState<boolean>(false);
  const [pipelineSummary, setPipelineSummary] = useState<CampaignRunSummary | null>(null);
  const [selectedModelForAsset, setSelectedModelForAsset] = useState<Record<string, string>>({});
  const [expandedInference, setExpandedInference] = useState<Record<string, boolean>>({});

  // Fetch enabled models on mount
  useEffect(() => {
    getModels(true)
      .then((models) => setEnabledModels(models))
      .catch(() => {});
  }, []);

  // Fetch processing status and inference runs for assets on load
  const loadAssetDetails = (assetList: Asset[]) => {
    assetList.forEach((asset) => {
      // 1. Processing info
      getAssetProcessing(asset.id)
        .then((record) => {
          if (record) {
            setProcessingMap((prev) => ({ ...prev, [asset.id]: record }));
            if (record.media_type === 'video' && record.status === 'completed') {
              getAssetFrames(asset.id)
                .then((res) => {
                  setVideoFramesMap((prev) => ({ ...prev, [asset.id]: res.frames }));
                })
                .catch(() => {});
            }
          }
        })
        .catch(() => {});

      // 2. Inference runs
      getAssetInferenceRuns(asset.id)
        .then((runs) => {
          setInferenceRunsMap((prev) => ({ ...prev, [asset.id]: runs }));
        })
        .catch(() => {});
    });
  };

  useEffect(() => {
    if (assets.length === 0) return;
    loadAssetDetails(assets);
  }, [assets]);

  const handleFilesSelected = async (e: ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const fileList = Array.from(e.target.files);
    e.target.value = '';

    try {
      setUploading(true);
      setError(null);
      setUploadProgress(`Uploading ${fileList.length} ${fileList.length === 1 ? 'file' : 'files'}...`);
      await onUploadFiles(fileList);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Upload failed');
      }
    } finally {
      setUploading(false);
      setUploadProgress(null);
    }
  };

  const handleProcessAsset = async (asset: Asset, force: boolean = false) => {
    try {
      setProcessingLoading((prev) => ({ ...prev, [asset.id]: true }));
      setError(null);
      const updated = await processAsset(asset.id, 1.0, force);
      setProcessingMap((prev) => ({ ...prev, [asset.id]: updated }));

      if (asset.media_type === 'video' && updated.status === 'completed') {
        const framesRes = await getAssetFrames(asset.id);
        setVideoFramesMap((prev) => ({ ...prev, [asset.id]: framesRes.frames }));
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Media processing failed');
      }
    } finally {
      setProcessingLoading((prev) => ({ ...prev, [asset.id]: false }));
    }
  };

  const handleRunPipeline = async () => {
    try {
      setPipelineRunning(true);
      setError(null);
      setPipelineSummary(null);
      const summary = await runCampaignPipeline(campaign.id);
      setPipelineSummary(summary);

      // Refresh all asset inference runs
      loadAssetDetails(assets);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Pipeline execution failed');
      }
    } finally {
      setPipelineRunning(false);
    }
  };

  const handleRunSingleModel = async (assetId: string) => {
    const modelId = selectedModelForAsset[assetId] || (enabledModels[0] ? enabledModels[0].id : '');
    if (!modelId) {
      setError('Please select an enabled model to run.');
      return;
    }

    try {
      setInferringMap((prev) => ({ ...prev, [assetId]: true }));
      setError(null);
      const run = await inferAsset(assetId, modelId);

      // Add to state
      setInferenceRunsMap((prev) => ({
        ...prev,
        [assetId]: [run, ...(prev[assetId] || []).filter((r) => r.id !== run.id)],
      }));

      // Automatically open the inference section
      setExpandedInference((prev) => ({ ...prev, [assetId]: true }));
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Model inference failed');
      }
    } finally {
      setInferringMap((prev) => ({ ...prev, [assetId]: false }));
    }
  };

  const toggleGallery = (assetId: string) => {
    setExpandedGallery((prev) => ({ ...prev, [assetId]: !prev[assetId] }));
  };

  const toggleInference = (assetId: string) => {
    setExpandedInference((prev) => ({ ...prev, [assetId]: !prev[assetId] }));
  };

  // Processable count: images are ready, videos must be completed
  const processableCount = assets.filter((a) => {
    if (a.media_type === 'image') return true;
    const proc = processingMap[a.id];
    return proc && proc.status === 'completed';
  }).length;

  return (
    <div className="campaign-details-container">
      <div className="view-header">
        <div>
          <button type="button" className="btn-link" onClick={onBack}>
            &larr; Back to Campaigns
          </button>
          <h2>{campaign.name}</h2>
          <p className="subtitle">
            Created on{' '}
            {new Date(campaign.created_at).toLocaleDateString(undefined, {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </p>
        </div>

        <div className="header-actions">
          {assets.length > 0 && (
            <div className="view-toggle">
              <button
                type="button"
                className={`toggle-btn ${viewMode === 'grid' ? 'active' : ''}`}
                onClick={() => setViewMode('grid')}
                title="Grid Preview"
              >
                Grid
              </button>
              <button
                type="button"
                className={`toggle-btn ${viewMode === 'table' ? 'active' : ''}`}
                onClick={() => setViewMode('table')}
                title="Table View"
              >
                List
              </button>
            </div>
          )}

          <input
            type="file"
            multiple
            ref={fileInputRef}
            onChange={handleFilesSelected}
            style={{ display: 'none' }}
            accept=".jpg,.jpeg,.png,.webp,.mp4,.mov,.webm"
          />
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
          >
            {uploading ? uploadProgress || 'Uploading...' : '+ Upload Assets'}
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          <span>{error}</span>
          <button type="button" className="alert-close" onClick={() => setError(null)}>
            &times;
          </button>
        </div>
      )}

      {/* Pipeline Control Section */}
      {assets.length > 0 && (
        <div className="card pipeline-card">
          <div className="pipeline-header">
            <div>
              <h3 style={{ margin: 0, fontSize: '1.15rem' }}>Model Inference Pipeline</h3>
              <p className="subtitle" style={{ margin: '0.25rem 0 0 0', fontSize: '0.85rem' }}>
                Run all enabled multimodal models against processable assets in this campaign.
              </p>
            </div>
            <button
              type="button"
              className="btn btn-primary btn-run-pipeline"
              onClick={handleRunPipeline}
              disabled={pipelineRunning || enabledModels.length === 0}
            >
              {pipelineRunning ? 'Running Pipeline...' : '▶ Run Pipeline'}
            </button>
          </div>

          <div className="pipeline-status-row">
            <div className="pipeline-info-group">
              <span className="pipeline-label">Enabled Models:</span>
              {enabledModels.length === 0 ? (
                <span className="text-muted" style={{ fontSize: '0.85rem' }}>
                  No enabled models. Please enable models in the Model Registry.
                </span>
              ) : (
                <div className="model-tag-list">
                  {enabledModels.map((m) => (
                    <span key={m.id} className="badge badge-neutral model-tag">
                      {m.name} ({m.provider})
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="pipeline-meta-stats">
              <span>
                Processable Assets: <strong>{processableCount}</strong> / {assets.length}
              </span>
            </div>
          </div>

          {pipelineSummary && (
            <div className="pipeline-summary-alert">
              <span>
                ✓ Pipeline executed: <strong>{pipelineSummary.runs_created}</strong> runs created across{' '}
                {pipelineSummary.assets} assets ({pipelineSummary.successful_runs || 0} completed
                {pipelineSummary.failed_runs ? `, ${pipelineSummary.failed_runs} failed` : ''}).
              </span>
            </div>
          )}
        </div>
      )}

      {loading ? (
        <div className="card loading-card">
          <div className="spinner"></div>
          <p>Loading assets...</p>
        </div>
      ) : assets.length === 0 ? (
        <div className="card empty-card">
          <p className="empty-title">No assets uploaded yet</p>
          <p className="empty-subtitle">
            Upload images (JPG, PNG, WebP) or videos (MP4, MOV, WebM) to this campaign.
          </p>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
          >
            Upload First Asset
          </button>
        </div>
      ) : viewMode === 'grid' ? (
        <div className="asset-grid">
          {assets.map((asset) => {
            const proc = processingMap[asset.id];
            const isProcessing = processingLoading[asset.id];
            const isInferring = inferringMap[asset.id];
            const frames = videoFramesMap[asset.id] || [];
            const isGalleryOpen = !!expandedGallery[asset.id];
            const runs = inferenceRunsMap[asset.id] || [];
            const isInferenceOpen = expandedInference[asset.id] !== false; // open by default if runs exist

            return (
              <div key={asset.id} className="card asset-card">
                <div className="asset-preview-container">
                  {asset.media_type === 'image' ? (
                    <div
                      className="image-wrapper"
                      onClick={() =>
                        setPreviewModalItem({
                          title: asset.filename,
                          mediaType: 'image',
                          url: getAssetFileUrl(asset.id),
                          details: `${formatFileSize(asset.file_size)} • ${
                            proc?.width && proc?.height ? `${proc.width}×${proc.height}` : ''
                          }`,
                        })
                      }
                      title="Click to view full image"
                    >
                      <img
                        src={getAssetFileUrl(asset.id)}
                        alt={asset.filename}
                        className="asset-thumbnail"
                        loading="lazy"
                      />
                    </div>
                  ) : (
                    <div className="video-wrapper">
                      <video
                        src={getAssetFileUrl(asset.id)}
                        controls
                        preload="metadata"
                        playsInline
                        className="asset-video-element"
                      />
                    </div>
                  )}
                </div>

                <div className="asset-info">
                  <div className="asset-title-row">
                    <span className="asset-filename" title={asset.filename}>
                      {asset.filename}
                    </span>
                    <span
                      className={`badge ${
                        asset.media_type === 'image' ? 'badge-image' : 'badge-video'
                      }`}
                    >
                      {asset.media_type}
                    </span>
                  </div>

                  <div className="asset-meta-row">
                    <span>{formatFileSize(asset.file_size)}</span>
                    <span>&bull;</span>
                    <span>
                      {new Date(asset.created_at).toLocaleDateString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                      })}
                    </span>
                  </div>

                  {/* Processing Status & Metadata Section */}
                  <div className="processing-section">
                    <div className="processing-status-row">
                      <span className="processing-label">Media:</span>
                      <span
                        className={`badge badge-status ${
                          isProcessing
                            ? 'badge-processing'
                            : proc?.status === 'completed'
                            ? 'badge-completed'
                            : proc?.status === 'failed'
                            ? 'badge-failed'
                            : 'badge-pending'
                        }`}
                      >
                        {isProcessing ? 'processing...' : proc?.status || 'unprocessed'}
                      </span>

                      <button
                        type="button"
                        className="btn btn-sm btn-process"
                        onClick={() => handleProcessAsset(asset, !!proc)}
                        disabled={isProcessing}
                      >
                        {isProcessing
                          ? 'Processing...'
                          : proc?.status === 'completed'
                          ? 'Re-process'
                          : 'Process'}
                      </button>
                    </div>

                    {proc?.status === 'completed' && (
                      <div className="metadata-badge-list">
                        {asset.media_type === 'image' && (
                          <>
                            {proc.width && proc.height && (
                              <span className="meta-pill">
                                {proc.width} × {proc.height}
                              </span>
                            )}
                            {proc.format && <span className="meta-pill">{proc.format}</span>}
                          </>
                        )}

                        {asset.media_type === 'video' && (
                          <>
                            {proc.width && proc.height && (
                              <span className="meta-pill">
                                {proc.width} × {proc.height}
                              </span>
                            )}
                            {proc.duration_ms && (
                              <span className="meta-pill">
                                {formatDuration(proc.duration_ms)}
                              </span>
                            )}
                            {proc.frame_rate && (
                              <span className="meta-pill">{proc.frame_rate} fps</span>
                            )}
                            {proc.frames_extracted !== null &&
                              proc.frames_extracted !== undefined && (
                                <span className="meta-pill">
                                  {proc.frames_extracted} frames
                                </span>
                              )}
                          </>
                        )}
                      </div>
                    )}

                    {proc?.status === 'failed' && (
                      <p className="processing-error-text">
                        Error: {proc.error_message || 'Processing failed'}
                      </p>
                    )}

                    {/* Extracted frames gallery for videos */}
                    {asset.media_type === 'video' &&
                      proc?.status === 'completed' &&
                      frames.length > 0 && (
                        <div className="frames-gallery-wrapper">
                          <button
                            type="button"
                            className="btn-link gallery-toggle-btn"
                            onClick={() => toggleGallery(asset.id)}
                          >
                            {isGalleryOpen ? '▲ Hide Frames' : `▼ View Extracted Frames (${frames.length})`}
                          </button>

                          {isGalleryOpen && (
                            <div className="frames-strip">
                              {frames.map((frame) => (
                                <div
                                  key={frame.filename}
                                  className="frame-strip-item"
                                  onClick={() =>
                                    setPreviewModalItem({
                                      title: `${asset.filename} — Frame #${frame.frame_number}`,
                                      mediaType: 'image',
                                      url: getFrameUrl(asset.id, frame.filename),
                                      details: frame.filename,
                                    })
                                  }
                                  title={`Click to view Frame #${frame.frame_number}`}
                                >
                                  <img
                                    src={getFrameUrl(asset.id, frame.filename)}
                                    alt={frame.filename}
                                    className="frame-strip-img"
                                    loading="lazy"
                                  />
                                  <span className="frame-strip-number">#{frame.frame_number}</span>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                  </div>

                  {/* Inference Results Section */}
                  <div className="inference-section">
                    <div className="inference-header-row">
                      <button
                        type="button"
                        className="btn-link inference-toggle-btn"
                        onClick={() => toggleInference(asset.id)}
                      >
                        {isInferenceOpen
                          ? `▲ Inference Runs (${runs.length})`
                          : `▼ View Inference Runs (${runs.length})`}
                      </button>

                      {enabledModels.length > 0 && (
                        <div className="run-model-dropdown-group">
                          <select
                            className="model-select"
                            value={selectedModelForAsset[asset.id] || enabledModels[0]?.id}
                            onChange={(e) =>
                              setSelectedModelForAsset((prev) => ({
                                ...prev,
                                [asset.id]: e.target.value,
                              }))
                            }
                            disabled={isInferring}
                          >
                            {enabledModels.map((m) => (
                              <option key={m.id} value={m.id}>
                                {m.name}
                              </option>
                            ))}
                          </select>
                          <button
                            type="button"
                            className="btn btn-sm btn-primary"
                            onClick={() => handleRunSingleModel(asset.id)}
                            disabled={isInferring}
                          >
                            {isInferring ? 'Running...' : 'Run'}
                          </button>
                        </div>
                      )}
                    </div>

                    {isInferenceOpen && (
                      <div className="inference-results-list">
                        {runs.length === 0 ? (
                          <p className="text-muted" style={{ fontSize: '0.78rem', margin: '0.25rem 0' }}>
                            No model runs yet. Use 'Run' above or 'Run Pipeline' to evaluate.
                          </p>
                        ) : (
                          runs.map((run) => {
                            const contextData = run.context || run.context_json;
                            const textOutput = run.text || run.response_text;
                            return (
                              <div key={run.id} className="inference-run-card">
                                <div className="run-card-top">
                                  <div className="run-model-meta">
                                    <strong>{run.model_name || 'Model'}</strong>
                                    {run.provider && (
                                      <span className="meta-pill" style={{ marginLeft: '0.35rem' }}>
                                        {run.provider}
                                      </span>
                                    )}
                                  </div>
                                  <span
                                    className={`badge badge-status ${
                                      run.status === 'completed'
                                        ? 'badge-completed'
                                        : run.status === 'failed'
                                        ? 'badge-failed'
                                        : 'badge-processing'
                                    }`}
                                  >
                                    {run.status}
                                  </span>
                                </div>

                                {run.status === 'completed' && (
                                  <>
                                    <div className="run-telemetry-row">
                                      {run.latency_ms && (
                                        <span className="telemetry-pill">
                                          ⏱ {(run.latency_ms / 1000).toFixed(2)}s
                                        </span>
                                      )}
                                      {run.estimated_cost_usd !== null &&
                                        run.estimated_cost_usd !== undefined && (
                                          <span className="telemetry-pill">
                                            💰 ${run.estimated_cost_usd.toFixed(4)}
                                          </span>
                                        )}
                                      {run.input_tokens && run.output_tokens && (
                                        <span className="telemetry-pill">
                                          🔤 {run.input_tokens} / {run.output_tokens} tok
                                        </span>
                                      )}
                                    </div>

                                    {textOutput && (
                                      <div className="inference-text-box">
                                        <strong>Text:</strong>
                                        <p>{textOutput}</p>
                                      </div>
                                    )}

                                    {contextData && (
                                      <div className="inference-context-box">
                                        <strong>Context:</strong>
                                        <div className="context-fields">
                                          {contextData.brand && (
                                            <div>
                                              <span className="context-key">Brand:</span>{' '}
                                              {contextData.brand}
                                            </div>
                                          )}
                                          {contextData.product && (
                                            <div>
                                              <span className="context-key">Product:</span>{' '}
                                              {contextData.product}
                                            </div>
                                          )}
                                          {contextData.offer && (
                                            <div>
                                              <span className="context-key">Offer:</span>{' '}
                                              {contextData.offer}
                                            </div>
                                          )}
                                          {contextData.cta && (
                                            <div>
                                              <span className="context-key">CTA:</span>{' '}
                                              {contextData.cta}
                                            </div>
                                          )}
                                          {contextData.summary && (
                                            <div>
                                              <span className="context-key">Summary:</span>{' '}
                                              {contextData.summary}
                                            </div>
                                          )}
                                        </div>
                                      </div>
                                    )}
                                  </>
                                )}

                                {run.status === 'failed' && (
                                  <p className="processing-error-text">
                                    Error: {run.error_message || 'Inference execution failed'}
                                  </p>
                                )}
                              </div>
                            );
                          })
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="assets-table-container card">
          <table className="assets-table">
            <thead>
              <tr>
                <th style={{ width: '80px' }}>Preview</th>
                <th>Filename</th>
                <th>Type</th>
                <th>Media Status</th>
                <th>Inference Runs</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {assets.map((asset) => {
                const proc = processingMap[asset.id];
                const isProcessing = processingLoading[asset.id];
                const isInferring = inferringMap[asset.id];
                const runs = inferenceRunsMap[asset.id] || [];

                return (
                  <tr key={asset.id}>
                    <td className="table-preview-cell">
                      {asset.media_type === 'image' ? (
                        <img
                          src={getAssetFileUrl(asset.id)}
                          alt={asset.filename}
                          className="table-thumbnail"
                          onClick={() =>
                            setPreviewModalItem({
                              title: asset.filename,
                              mediaType: 'image',
                              url: getAssetFileUrl(asset.id),
                            })
                          }
                        />
                      ) : (
                        <video
                          src={getAssetFileUrl(asset.id)}
                          preload="metadata"
                          className="table-video-thumb"
                          onClick={() =>
                            setPreviewModalItem({
                              title: asset.filename,
                              mediaType: 'video',
                              url: getAssetFileUrl(asset.id),
                            })
                          }
                        />
                      )}
                    </td>
                    <td className="asset-filename">
                      <strong>{asset.filename}</strong>
                      <div className="asset-size">{formatFileSize(asset.file_size)}</div>
                    </td>
                    <td>
                      <span
                        className={`badge ${
                          asset.media_type === 'image' ? 'badge-image' : 'badge-video'
                        }`}
                      >
                        {asset.media_type}
                      </span>
                    </td>
                    <td>
                      <span
                        className={`badge badge-status ${
                          isProcessing
                            ? 'badge-processing'
                            : proc?.status === 'completed'
                            ? 'badge-completed'
                            : proc?.status === 'failed'
                            ? 'badge-failed'
                            : 'badge-pending'
                        }`}
                      >
                        {isProcessing ? 'processing...' : proc?.status || 'unprocessed'}
                      </span>
                    </td>
                    <td>
                      <div className="table-meta">
                        <span>{runs.length} runs</span>
                        {runs.slice(0, 2).map((r) => (
                          <span key={r.id} style={{ fontSize: '0.75rem' }}>
                            {r.model_name || 'Model'}: {r.status}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                        <button
                          type="button"
                          className="btn btn-sm btn-secondary"
                          onClick={() => handleProcessAsset(asset, !!proc)}
                          disabled={isProcessing}
                        >
                          {isProcessing ? '...' : proc?.status === 'completed' ? 'Re-process' : 'Process'}
                        </button>
                        {enabledModels.length > 0 && (
                          <button
                            type="button"
                            className="btn btn-sm btn-primary"
                            onClick={() => handleRunSingleModel(asset.id)}
                            disabled={isInferring}
                          >
                            {isInferring ? '...' : 'Infer'}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal preview dialog */}
      {previewModalItem && (
        <div className="modal-backdrop" onClick={() => setPreviewModalItem(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{previewModalItem.title}</h3>
              <button
                type="button"
                className="modal-close"
                onClick={() => setPreviewModalItem(null)}
              >
                &times;
              </button>
            </div>
            <div className="modal-body">
              {previewModalItem.mediaType === 'image' ? (
                <img
                  src={previewModalItem.url}
                  alt={previewModalItem.title}
                  className="modal-image"
                />
              ) : (
                <video
                  src={previewModalItem.url}
                  controls
                  autoPlay
                  className="modal-video"
                />
              )}
            </div>
            {previewModalItem.details && (
              <div className="modal-footer">
                <span>{previewModalItem.details}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
