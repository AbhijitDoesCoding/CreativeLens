import { useRef, useState, type ChangeEvent } from 'react';
import type { Asset, Campaign } from '../types';
import { getAssetFileUrl } from '../services/api';

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
  const [previewModalAsset, setPreviewModalAsset] = useState<Asset | null>(null);

  const handleFilesSelected = async (e: ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const fileList = Array.from(e.target.files);
    e.target.value = ''; // Reset input to allow re-uploading same file

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
          {assets.map((asset) => (
            <div key={asset.id} className="card asset-card">
              <div className="asset-preview-container">
                {asset.media_type === 'image' ? (
                  <div
                    className="image-wrapper"
                    onClick={() => setPreviewModalAsset(asset)}
                    title="Click to expand"
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
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="assets-table-container card">
          <table className="assets-table">
            <thead>
              <tr>
                <th style={{ width: '80px' }}>Preview</th>
                <th>Filename</th>
                <th>Type</th>
                <th>Size</th>
                <th>Upload Date</th>
              </tr>
            </thead>
            <tbody>
              {assets.map((asset) => (
                <tr key={asset.id}>
                  <td className="table-preview-cell">
                    {asset.media_type === 'image' ? (
                      <img
                        src={getAssetFileUrl(asset.id)}
                        alt={asset.filename}
                        className="table-thumbnail"
                        onClick={() => setPreviewModalAsset(asset)}
                      />
                    ) : (
                      <video
                        src={getAssetFileUrl(asset.id)}
                        preload="metadata"
                        className="table-video-thumb"
                        onClick={() => setPreviewModalAsset(asset)}
                      />
                    )}
                  </td>
                  <td className="asset-filename">
                    <strong>{asset.filename}</strong>
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
                  <td className="asset-size">{formatFileSize(asset.file_size)}</td>
                  <td className="asset-date">
                    {new Date(asset.created_at).toLocaleString(undefined, {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal preview dialog */}
      {previewModalAsset && (
        <div className="modal-backdrop" onClick={() => setPreviewModalAsset(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{previewModalAsset.filename}</h3>
              <button
                type="button"
                className="modal-close"
                onClick={() => setPreviewModalAsset(null)}
              >
                &times;
              </button>
            </div>
            <div className="modal-body">
              {previewModalAsset.media_type === 'image' ? (
                <img
                  src={getAssetFileUrl(previewModalAsset.id)}
                  alt={previewModalAsset.filename}
                  className="modal-image"
                />
              ) : (
                <video
                  src={getAssetFileUrl(previewModalAsset.id)}
                  controls
                  autoPlay
                  className="modal-video"
                />
              )}
            </div>
            <div className="modal-footer">
              <span
                className={`badge ${
                  previewModalAsset.media_type === 'image' ? 'badge-image' : 'badge-video'
                }`}
              >
                {previewModalAsset.media_type}
              </span>
              <span>{formatFileSize(previewModalAsset.file_size)}</span>
              <span>
                Uploaded on{' '}
                {new Date(previewModalAsset.created_at).toLocaleString(undefined, {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
