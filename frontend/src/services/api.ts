import type { Asset, Campaign, HealthStatus } from '../types';

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
