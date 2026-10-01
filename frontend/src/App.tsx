import { useEffect, useState } from 'react';
import { CampaignList } from './components/CampaignList';
import { CreateCampaign } from './components/CreateCampaign';
import { CampaignDetails } from './components/CampaignDetails';
import { ModelManagement } from './components/ModelManagement';
import {
  createCampaign,
  createModel,
  disableModel,
  enableModel,
  getCampaign,
  getCampaignAssets,
  getCampaigns,
  getModels,
  updateModel,
  uploadCampaignAsset,
} from './services/api';
import type {
  Asset,
  Campaign,
  CreateModelInput,
  Model,
  UpdateModelInput,
} from './types';
import './App.css';

type ViewMode = 'list' | 'create' | 'details' | 'models';

export default function App() {
  const [view, setView] = useState<ViewMode>('list');
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [loadingCampaigns, setLoadingCampaigns] = useState<boolean>(true);
  const [loadingAssets, setLoadingAssets] = useState<boolean>(false);
  const [loadingModels, setLoadingModels] = useState<boolean>(false);
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

  const fetchModels = async () => {
    try {
      setLoadingModels(true);
      const data = await getModels();
      setModels(data);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to load models.');
      }
    } finally {
      setLoadingModels(false);
    }
  };

  useEffect(() => {
    fetchCampaigns();
    fetchModels();
  }, []);

  const handleOpenCampaign = async (campaignId: string) => {
    try {
      setError(null);
      setLoadingAssets(true);
      setView('details');

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
    await fetchCampaigns();
    await handleOpenCampaign(newCampaign.id);
  };

  const handleUploadFiles = async (files: File[]) => {
    if (!selectedCampaign) return;

    for (const file of files) {
      await uploadCampaignAsset(selectedCampaign.id, file);
    }

    const updatedAssets = await getCampaignAssets(selectedCampaign.id);
    setAssets(updatedAssets);

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

  const handleCreateModel = async (data: CreateModelInput) => {
    await createModel(data);
    await fetchModels();
  };

  const handleUpdateModel = async (modelId: string, data: UpdateModelInput) => {
    await updateModel(modelId, data);
    await fetchModels();
  };

  const handleEnableModel = async (modelId: string) => {
    await enableModel(modelId);
    await fetchModels();
  };

  const handleDisableModel = async (modelId: string) => {
    await disableModel(modelId);
    await fetchModels();
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-brand" onClick={handleBackToList} style={{ cursor: 'pointer' }}>
          <h1>CreativeLens</h1>
          <p className="subtitle">Marketing Creative Evaluation Platform</p>
        </div>

        <nav className="header-nav">
          <button
            type="button"
            className={`nav-tab ${view !== 'models' ? 'active' : ''}`}
            onClick={handleBackToList}
          >
            Campaigns
          </button>
          <button
            type="button"
            className={`nav-tab ${view === 'models' ? 'active' : ''}`}
            onClick={() => {
              setView('models');
              setSelectedCampaign(null);
              fetchModels();
            }}
          >
            Model Registry
          </button>
        </nav>
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

        {view === 'models' && (
          <ModelManagement
            models={models}
            loading={loadingModels}
            onRefresh={fetchModels}
            onCreateModel={handleCreateModel}
            onUpdateModel={handleUpdateModel}
            onEnableModel={handleEnableModel}
            onDisableModel={handleDisableModel}
          />
        )}
      </main>
    </div>
  );
}
