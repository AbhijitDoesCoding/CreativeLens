import { useEffect, useState } from 'react';
import { CampaignList } from './components/CampaignList';
import { CreateCampaign } from './components/CreateCampaign';
import { CampaignDetails } from './components/CampaignDetails';
import {
  createCampaign,
  getCampaign,
  getCampaignAssets,
  getCampaigns,
  uploadCampaignAsset,
} from './services/api';
import type { Asset, Campaign } from './types';
import './App.css';

type ViewMode = 'list' | 'create' | 'details';

export default function App() {
  const [view, setView] = useState<ViewMode>('list');
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loadingCampaigns, setLoadingCampaigns] = useState<boolean>(true);
  const [loadingAssets, setLoadingAssets] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCampaigns = async () => {
    try {
      setLoadingCampaigns(true);
      setError(null);
      const data = await getCampaigns();
      setCampaigns(data);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to load campaigns.');
      }
    } finally {
      setLoadingCampaigns(false);
    }
  };

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const handleOpenCampaign = async (campaignId: string) => {
    try {
      setError(null);
      setLoadingAssets(true);
      setView('details');

      // Fetch campaign and its assets concurrently
      const [campaignData, assetsData] = await Promise.all([
        getCampaign(campaignId),
        getCampaignAssets(campaignId),
      ]);
      setSelectedCampaign(campaignData);
      setAssets(assetsData);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to open campaign.');
      }
      setView('list');
    } finally {
      setLoadingAssets(false);
    }
  };

  const handleCreateCampaign = async (name: string) => {
    const newCampaign = await createCampaign(name);
    // Refresh campaign list
    await fetchCampaigns();
    // Open the new campaign
    await handleOpenCampaign(newCampaign.id);
  };

  const handleUploadFiles = async (files: File[]) => {
    if (!selectedCampaign) return;

    for (const file of files) {
      await uploadCampaignAsset(selectedCampaign.id, file);
    }

    // Refresh assets for this campaign
    const updatedAssets = await getCampaignAssets(selectedCampaign.id);
    setAssets(updatedAssets);

    // Update campaign asset count in state
    setSelectedCampaign((prev) =>
      prev ? { ...prev, asset_count: updatedAssets.length } : null
    );
  };

  const handleBackToList = () => {
    setView('list');
    setSelectedCampaign(null);
    setAssets([]);
    fetchCampaigns();
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-brand" onClick={handleBackToList} style={{ cursor: 'pointer' }}>
          <h1>CreativeLens</h1>
          <p className="subtitle">Marketing Creative Evaluation Platform</p>
        </div>
      </header>

      {error && (
        <div className="alert alert-error">
          <span>{error}</span>
          <button type="button" className="alert-close" onClick={() => setError(null)}>
            &times;
          </button>
        </div>
      )}

      <main className="main-content">
        {view === 'list' && (
          <CampaignList
            campaigns={campaigns}
            loading={loadingCampaigns}
            onSelectCampaign={handleOpenCampaign}
            onOpenCreate={() => setView('create')}
          />
        )}

        {view === 'create' && (
          <CreateCampaign
            onSubmit={handleCreateCampaign}
            onCancel={() => setView('list')}
          />
        )}

        {view === 'details' && selectedCampaign && (
          <CampaignDetails
            campaign={selectedCampaign}
            assets={assets}
            loading={loadingAssets}
            onBack={handleBackToList}
            onUploadFiles={handleUploadFiles}
          />
        )}
      </main>
    </div>
  );
}
