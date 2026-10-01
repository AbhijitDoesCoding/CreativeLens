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

export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface MediaProcessing {
  id: string;
  asset_id: string;
  media_type: MediaType;
  status: ProcessingStatus;
  width?: number | null;
  height?: number | null;
  format?: string | null;
  color_mode?: string | null;
  duration_ms?: number | null;
  frame_rate?: number | null;
  total_frames?: number | null;
  frames_extracted?: number | null;
  frame_directory?: string | null;
  processed_at?: string | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface FrameInfo {
  frame_number: number;
  filename: string;
  url: string;
}

export interface AssetFramesResponse {
  asset_id: string;
  total_frames: number;
  frame_directory?: string | null;
  frames: FrameInfo[];
}

export interface Model {
  id: string;
  name: string;
  provider: string;
  model_key: string;
  model_type: string;
  enabled: boolean;
  configuration_json?: Record<string, any> | null;
  pricing_json?: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

export interface CreateModelInput {
  name: string;
  provider: string;
  model_key: string;
  model_type?: string;
  enabled?: boolean;
  configuration_json?: Record<string, any> | null;
  pricing_json?: Record<string, any> | null;
}

export interface UpdateModelInput {
  name?: string;
  provider?: string;
  model_key?: string;
  model_type?: string;
  enabled?: boolean;
  configuration_json?: Record<string, any> | null;
  pricing_json?: Record<string, any> | null;
}

