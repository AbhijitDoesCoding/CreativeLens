import type { Campaign } from '../types';

interface CampaignListProps {
  campaigns: Campaign[];
  loading: boolean;
  onSelectCampaign: (campaignId: string) => void;
  onOpenCreate: () => void;
}

export function CampaignList({
  campaigns,
  loading,
  onSelectCampaign,
  onOpenCreate,
}: CampaignListProps) {
  if (loading) {
    return (
      <div className="card loading-card">
        <div className="spinner"></div>
        <p>Loading campaigns...</p>
      </div>
    );
  }

  return (
    <div className="campaign-list-container">
      <div className="view-header">
        <div>
          <h2>Campaigns</h2>
          <p className="subtitle">Manage campaigns and marketing creative assets</p>
        </div>
        <button type="button" className="btn btn-primary" onClick={onOpenCreate}>
          + Create Campaign
        </button>
      </div>

      {campaigns.length === 0 ? (
        <div className="card empty-card">
          <p className="empty-title">No campaigns yet</p>
          <p className="empty-subtitle">
            Get started by creating your first marketing campaign to upload creative assets.
          </p>
          <button type="button" className="btn btn-primary" onClick={onOpenCreate}>
            Create First Campaign
          </button>
        </div>
      ) : (
        <div className="campaign-grid">
          {campaigns.map((campaign) => (
            <div key={campaign.id} className="card campaign-card">
              <div className="campaign-card-header">
                <h3 className="campaign-name">{campaign.name}</h3>
                <span className="badge badge-neutral">
                  {campaign.asset_count ?? 0} {campaign.asset_count === 1 ? 'asset' : 'assets'}
                </span>
              </div>
              <div className="campaign-card-body">
                <div className="metadata-row">
                  <span className="label">Created:</span>
                  <span className="value">
                    {new Date(campaign.created_at).toLocaleDateString(undefined, {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                    })}
                  </span>
                </div>
              </div>
              <div className="campaign-card-footer">
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={() => onSelectCampaign(campaign.id)}
                >
                  Open Campaign &rarr;
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
