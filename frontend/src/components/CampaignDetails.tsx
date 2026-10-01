import { useRef, useState, type ChangeEvent } from 'react';
import type { Asset, Campaign } from '../types';

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

  const handleFilesSelected = async (e: ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const fileList = Array.from(e.target.files);
    e.target.value = ''; // Reset input to allow re-upload of same file name

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
            Created on {new Date(campaign.created_at).toLocaleDateString(undefined, {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </p>
        </div>

        <div className="header-actions">
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
      ) : (
        <div className="assets-table-container card">
          <table className="assets-table">
            <thead>
              <tr>
                <th>Filename</th>
                <th>Type</th>
                <th>Size</th>
                <th>Upload Date</th>
              </tr>
            </thead>
            <tbody>
              {assets.map((asset) => (
                <tr key={asset.id}>
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
    </div>
  );
}
