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

export interface ModelContextData {
  brand?: string | null;
  product?: string | null;
  offer?: string | null;
  cta?: string | null;
  summary?: string | null;
}

export interface InferenceRun {
  id: string;
  asset_id: string;
  model_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  text?: string | null;
  context?: ModelContextData | null;
  response_text?: string | null;
  context_json?: ModelContextData | null;
  started_at?: string | null;
  completed_at?: string | null;
  latency_ms?: number | null;
  ttft_ms?: number | null;
  input_tokens?: number | null;
  output_tokens?: number | null;
  estimated_cost_usd?: number | null;
  error_message?: string | null;
  created_at: string;
  model_name?: string | null;
  model_key?: string | null;
  provider?: string | null;
}

export interface CampaignRunSummary {
  campaign_id: string;
  assets: number;
  enabled_models: number;
  runs_created: number;
  successful_runs?: number | null;
  failed_runs?: number | null;
}


