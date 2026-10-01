import { useEffect, useRef, useState, type ChangeEvent } from 'react';
import type { Asset, Campaign, FrameInfo, MediaProcessing } from '../types';
import {
  getAssetFileUrl,
  getAssetFrames,
  getAssetProcessing,
  getFrameUrl,
  processAsset,
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

  // Fetch processing status for assets on load
  useEffect(() => {
    if (assets.length === 0) return;

    let isMounted = true;
    assets.forEach((asset) => {
      getAssetProcessing(asset.id)
        .then((record) => {
          if (isMounted && record) {
            setProcessingMap((prev) => ({ ...prev, [asset.id]: record }));
            if (record.media_type === 'video' && record.status === 'completed') {
              getAssetFrames(asset.id)
                .then((res) => {
                  if (isMounted) {
                    setVideoFramesMap((prev) => ({ ...prev, [asset.id]: res.frames }));
                  }
                })
                .catch(() => {});
            }
          }
        })
        .catch(() => {});
    });

    return () => {
      isMounted = false;
    };
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

      const result = await processAsset(asset.id, 1.0, force);
      setProcessingMap((prev) => ({ ...prev, [asset.id]: result }));

      // If video, also fetch extracted frames
      if (result.media_type === 'video' && result.status === 'completed') {
        const framesRes = await getAssetFrames(asset.id);
        setVideoFramesMap((prev) => ({ ...prev, [asset.id]: framesRes.frames }));
        setExpandedGallery((prev) => ({ ...prev, [asset.id]: true }));
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(`Processing failed: ${err.message}`);
      } else {
        setError('Failed to process asset');
      }
    } finally {
      setProcessingLoading((prev) => ({ ...prev, [asset.id]: false }));
    }
  };

  const toggleGallery = (assetId: string) => {
    setExpandedGallery((prev) => ({ ...prev, [assetId]: !prev[assetId] }));
  };

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
            const frames = videoFramesMap[asset.id] || [];
            const isGalleryOpen = !!expandedGallery[asset.id];

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
                      <span className="processing-label">Status:</span>
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

                    {/* Metadata details */}
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

                    {/* Extracted frames gallery toggle for videos */}
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
                <th>Metadata</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {assets.map((asset) => {
                const proc = processingMap[asset.id];
                const isProcessing = processingLoading[asset.id];

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
                      {proc?.status === 'completed' ? (
                        <div className="table-meta">
                          {proc.width && proc.height && (
                            <div>
                              {proc.width} × {proc.height}
                            </div>
                          )}
                          {proc.format && <div>Format: {proc.format}</div>}
                          {proc.duration_ms && (
                            <div>Duration: {formatDuration(proc.duration_ms)}</div>
                          )}
                          {proc.frames_extracted !== null && proc.frames_extracted !== undefined && (
                            <div>Frames: {proc.frames_extracted}</div>
                          )}
                        </div>
                      ) : (
                        <span className="text-muted">—</span>
                      )}
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
                      <button
                        type="button"
                        className="btn btn-sm btn-secondary"
                        onClick={() => handleProcessAsset(asset, !!proc)}
                        disabled={isProcessing}
                      >
                        {isProcessing ? '...' : proc?.status === 'completed' ? 'Re-process' : 'Process'}
                      </button>
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
