import axios from 'axios';

const API_URL =
  (typeof process !== 'undefined' && process.env.NEXT_PUBLIC_API_URL) ||
  'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.response.use(
  response => response,
  error => {
    if (error.code === 'ECONNABORTED' || error.code === 'ERR_CANCELED') {
      console.warn('Request timeout/cancelled:', error.config?.url);
    }
    return Promise.reject(error);
  }
);

export interface UploadResponse {
  id: string;
  original_filename: string;
  file_type: string;
  status: string;
}

export interface ProcessingResult {
  id: string;
  original_filename: string;
  file_type: string;
  total_pages?: string;
  image_urls: string[];
  ocr_text: string;
  translated_text: string;
  upload_time: string;
  status: string;
  content_title?: string;
  ocr_model_id?: string;
  translate_model_id?: string;
  doc_language?: string;
  model_endpoint?: string;
}

export const uploadFile = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

export const deleteHistory = async (id: string): Promise<void> => {
  await api.delete(`/history/${id}`);
};

export const getResult = async (id: string): Promise<ProcessingResult> => {
  const response = await api.get(`/result/${id}`, { timeout: 10000 });
  return response.data;
};

export const getHistory = async (page: number = 1, pageSize: number = 20) => {
  const response = await api.get(`/history?page=${page}&page_size=${pageSize}`, { timeout: 10000 });
  return response.data;
};

export const updateContentTitle = async (id: string, contentTitle: string): Promise<{ id: string; content_title: string }> => {
  const response = await api.patch(`/result/${id}/title`, { content_title: contentTitle });
  return response.data;
};

export const autoGenerateTitle = async (id: string): Promise<{ id: string; content_title: string | null; generated: boolean }> => {
  const response = await api.post(`/result/${id}/auto-title`);
  return response.data;
};

export const updateRecordModel = async (id: string, ocrModelId?: string, translateModelId?: string): Promise<{ id: string; ocr_model_id: string; translate_model_id: string }> => {
  const data: any = {};
  if (ocrModelId !== undefined) data.ocr_model_id = ocrModelId;
  if (translateModelId !== undefined) data.translate_model_id = translateModelId;
  const response = await api.patch(`/result/${id}/model`, data);
  return response.data;
};

export const resetProcessing = async (id: string): Promise<void> => {
  await api.post(`/result/${id}/reset`, {}, { timeout: 60000 });
};

export const reprocessOcr = async (id: string, page: number, ocrModelId: string, endpoint: string, docLanguage: string): Promise<void> => {
  await api.post(`/result/${id}/reprocess-ocr?page=${page}`, {
    ocr_model_id: ocrModelId,
    endpoint: endpoint,
    doc_language: docLanguage
  }, { timeout: 300000 });
};

export const reprocessTranslate = async (id: string, page: number, translateModelId: string, endpoint: string): Promise<void> => {
  await api.post(`/result/${id}/reprocess-translate?page=${page}`, {
    translate_model_id: translateModelId,
    endpoint: endpoint
  }, { timeout: 300000 });
};

export const continueProcessing = async (id: string, ocrModelId: string, translateModelId: string, endpoint: string, docLanguage: string): Promise<{ message: string; status: string }> => {
  const response = await api.post(`/result/${id}/continue`, {
    ocr_model_id: ocrModelId,
    translate_model_id: translateModelId,
    endpoint: endpoint,
    doc_language: docLanguage
  }, { timeout: 600000 });
  return response.data;
};

export const exportOcrResult = async (id: string): Promise<Blob> => {
  const response = await api.get(`/export/${id}/ocr`, { responseType: 'blob' });
  return response.data;
};

export const exportTranslateResult = async (id: string): Promise<Blob> => {
  const response = await api.get(`/export/${id}/translate`, { responseType: 'blob' });
  return response.data;
};

export const getConfig = async (): Promise<{ model_endpoint: string }> => {
  const response = await api.get('/config');
  return response.data;
};

export const updateConfig = async (config: { model_endpoint: string }): Promise<void> => {
  await api.post('/config', config);
};

export interface Provider {
  id: number;
  name: string;
  display_name: string;
  base_url: string;
  api_key?: string | null;
  is_active: string;
  models: ModelEntry[];
}

export interface ModelEntry {
  id?: number;
  model_id: string;
  display_name: string;
  model_type: string;
  is_default: string;
  is_active: string;
}

export interface ExtendedConfig {
  model_endpoint: string;
  doc_language: string;
  ocr_model_id?: string | null;
  translate_model_id?: string | null;
  providers?: any[];
}

export interface ProviderSummary {
  id: number;
  name: string;
  display_name: string;
  base_url: string;
  is_active: string;
}

export const getProviders = async (): Promise<Provider[]> => {
  const response = await api.get('/providers', { timeout: 10000 });
  return response.data;
};

export const createProvider = async (data: { name: string; display_name?: string; base_url: string; api_key?: string; models?: Array<{ id: string; name: string }> }): Promise<Provider> => {
  const response = await api.post('/providers', data);
  return response.data;
};

export const updateProvider = async (id: number, data: { name?: string; display_name?: string; base_url?: string; api_key?: string }): Promise<Provider> => {
  const response = await api.put(`/providers/${id}`, data);
  return response.data;
};

export const deleteProvider = async (id: number): Promise<void> => {
  await api.delete(`/providers/${id}`);
};

export const updateProviderModels = async (id: number, data: any): Promise<Provider> => {
  const response = await api.put(`/providers/${id}/models`, data);
  return response.data;
};

export const toggleModel = async (modelId: number, isActive: string): Promise<any> => {
  const response = await api.patch(`/providers/models/${modelId}/toggle`, { is_active: isActive });
  return response.data;
};

export const fetchModelsFromProvider = async (data: { base_url: string; api_key?: string; name?: string }): Promise<any> => {
  const response = await api.post('/providers/fetch-models', data);
  return response.data;
};

export const getProviderModels = async (id: number): Promise<ModelEntry[]> => {
  const response = await api.get(`/providers/${id}/models`);
  return response.data;
};

export const testProviderConnection = async (id: number): Promise<{ status: string; message: string }> => {
  const response = await api.post(`/providers/${id}/test`);
  return response.data;
};

export const getExtendedConfig = async (): Promise<ExtendedConfig> => {
  const response = await api.get('/config');
  return response.data;
};

export const updateExtendedConfig = async (config: {
  doc_language?: string;
  ocr_model_id?: string | null;
  translate_model_id?: string | null;
}): Promise<void> => {
  await api.post('/config', config);
};

export const pauseOcr = async (id: string): Promise<{ message: string; last_page: number }> => {
  const response = await api.post(`/result/${id}/pause-ocr`);
  return response.data;
};

export const resumeOcr = async (id: string): Promise<{ message: string }> => {
  const response = await api.post(`/result/${id}/resume-ocr`);
  return response.data;
};

export const pauseTranslate = async (id: string): Promise<{ message: string }> => {
  const response = await api.post(`/result/${id}/pause-translate`);
  return response.data;
};

export const resumeTranslate = async (id: string): Promise<{ message: string }> => {
  const response = await api.post(`/result/${id}/resume-translate`);
  return response.data;
};

export default api;
