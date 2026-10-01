export interface HealthStatus {
  status: string;
}

export type MediaType = 'image' | 'video';

export interface Campaign {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  asset_count?: number;
}

export interface Asset {
  id: string;
  campaign_id: string;
  filename: string;
  file_path: string;
  media_type: MediaType;
  mime_type: string;
  file_size: number;
  created_at: string;
}

export interface CreateCampaignInput {
  name: string;
}
