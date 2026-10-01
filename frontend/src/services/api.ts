import type {
  Asset,
  AssetFramesResponse,
  Campaign,
  CampaignRunSummary,
  CreateModelInput,
  HealthStatus,
  InferenceRun,
  MediaProcessing,
  Model,
  UpdateModelInput,
} from '../types';



const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function checkHealth(): Promise<HealthStatus> {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.statusText}`);
  }
  return response.json();
}

export async function getCampaigns(): Promise<Campaign[]> {
  const response = await fetch(`${API_BASE_URL}/campaigns`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch campaigns (${response.status})`);
  }
  return response.json();
}

export async function getCampaign(campaignId: string): Promise<Campaign> {
  const response = await fetch(`${API_BASE_URL}/campaigns/${campaignId}`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch campaign (${response.status})`);
  }
  return response.json();
}

export async function createCampaign(name: string): Promise<Campaign> {
  const response = await fetch(`${API_BASE_URL}/campaigns`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ name }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    let msg = errorData.detail || `Failed to create campaign (${response.status})`;
    if (Array.isArray(errorData.detail)) {
      msg = errorData.detail.map((e: { msg?: string }) => e.msg).join(', ');
    }
    throw new Error(msg);
  }
  return response.json();
}

export async function getCampaignAssets(campaignId: string): Promise<Asset[]> {
  const response = await fetch(`${API_BASE_URL}/campaigns/${campaignId}/assets`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch assets (${response.status})`);
  }
  return response.json();
}

export async function uploadCampaignAsset(campaignId: string, file: File): Promise<Asset> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/campaigns/${campaignId}/assets`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    let msg = errorData.detail || `Failed to upload file "${file.name}" (${response.status})`;
    if (Array.isArray(errorData.detail)) {
      msg = errorData.detail.map((e: { msg?: string }) => e.msg).join(', ');
    }
    throw new Error(msg);
  }
  return response.json();
}

export function getAssetFileUrl(assetId: string): string {
  return `${API_BASE_URL}/assets/${assetId}/file`;
}

export async function processAsset(
  assetId: string,
  sampleFps: number = 1.0,
  force: boolean = false
): Promise<MediaProcessing> {
  const response = await fetch(`${API_BASE_URL}/assets/${assetId}/process`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ sample_fps: sampleFps, force }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Processing failed (${response.status})`);
  }
  return response.json();
}

export async function getAssetProcessing(assetId: string): Promise<MediaProcessing | null> {
  const response = await fetch(`${API_BASE_URL}/assets/${assetId}/processing`);
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch processing status (${response.status})`);
  }
  return response.json();
}

export async function getAssetFrames(assetId: string): Promise<AssetFramesResponse> {
  const response = await fetch(`${API_BASE_URL}/assets/${assetId}/frames`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch asset frames (${response.status})`);
  }
  return response.json();
}

export function getFrameUrl(assetId: string, frameFilename: string): string {
  return `${API_BASE_URL}/assets/${assetId}/frames/${frameFilename}`;
}

export async function getModels(enabledOnly: boolean = false): Promise<Model[]> {
  const url = enabledOnly ? `${API_BASE_URL}/models?enabled_only=true` : `${API_BASE_URL}/models`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch models (${response.status})`);
  }
  return response.json();
}

export async function getModel(modelId: string): Promise<Model> {
  const response = await fetch(`${API_BASE_URL}/models/${modelId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch model (${response.status})`);
  }
  return response.json();
}

export async function createModel(data: CreateModelInput): Promise<Model> {
  const response = await fetch(`${API_BASE_URL}/models`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to create model (${response.status})`);
  }
  return response.json();
}

export async function updateModel(modelId: string, data: UpdateModelInput): Promise<Model> {
  const response = await fetch(`${API_BASE_URL}/models/${modelId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to update model (${response.status})`);
  }
  return response.json();
}

export async function enableModel(modelId: string): Promise<Model> {
  const response = await fetch(`${API_BASE_URL}/models/${modelId}/enable`, {
    method: 'POST',
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to enable model (${response.status})`);
  }
  return response.json();
}

export async function disableModel(modelId: string): Promise<Model> {
  const response = await fetch(`${API_BASE_URL}/models/${modelId}/disable`, {
    method: 'POST',
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to disable model (${response.status})`);
  }
  return response.json();
}

export async function inferAsset(
  assetId: string,
  modelId: string,
  prompt?: string
): Promise<InferenceRun> {
  const response = await fetch(`${API_BASE_URL}/assets/${assetId}/infer/${modelId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt: prompt || null }),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Inference failed (${response.status})`);
  }
  return response.json();
}

export async function getAssetInferenceRuns(assetId: string): Promise<InferenceRun[]> {
  const response = await fetch(`${API_BASE_URL}/assets/${assetId}/inference-runs`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch inference runs (${response.status})`);
  }
  return response.json();
}

export async function getInferenceRun(runId: string): Promise<InferenceRun> {
  const response = await fetch(`${API_BASE_URL}/inference-runs/${runId}`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch inference run (${response.status})`);
  }
  return response.json();
}

export async function runCampaignPipeline(
  campaignId: string,
  prompt?: string,
  maxWorkers: number = 3
): Promise<CampaignRunSummary> {
  const response = await fetch(`${API_BASE_URL}/campaigns/${campaignId}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt: prompt || null, max_workers: maxWorkers }),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Pipeline run failed (${response.status})`);
  }
  return response.json();
}


