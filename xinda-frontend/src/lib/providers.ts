import { API_BASE } from './api';

export interface ModelEntry {
  id?: number;
  model_id: string;
  display_name: string;
  model_type: string;
  is_default: string;
  is_active: string;
}

export interface Provider {
  id: number;
  name: string;
  display_name: string;
  base_url: string;
  api_key?: string | null;
  is_active: string;
  models: ModelEntry[];
}

export interface ProviderSummary {
  id: number;
  name: string;
  display_name: string;
  base_url: string;
  is_active: string;
}

export interface ExtendedConfig {
  model_endpoint: string;
  doc_language: string;
  ocr_model_id: string | null;
  translate_model_id: string | null;
  providers: ProviderSummary[];
}

export interface CreateProviderData {
  name: string;
  display_name?: string;
  base_url: string;
  api_key?: string;
  models?: Array<{ id: string; name: string }>;
}

export interface UpdateProviderData {
  name?: string;
  display_name?: string;
  base_url?: string;
  api_key?: string;
  is_active?: string;
}

export const PRESET_PROVIDERS = [
  {
    name: 'ollama',
    displayName: 'Ollama',
    baseUrlPattern: 'http://localhost:11434',
  },
  {
    name: 'openai',
    displayName: 'OpenAI',
    baseUrlPattern: 'https://api.openai.com/v1',
  },
  {
    name: 'anthropic',
    displayName: 'Anthropic',
    baseUrlPattern: 'https://api.anthropic.com/v1',
  },
  {
    name: 'google',
    displayName: 'Google',
    baseUrlPattern: 'https://generativelanguage.googleapis.com/v1beta',
  },
] as const;

export function getModelTypeLabel(type: string): string {
  switch (type) {
    case 'ocr':
      return '识别';
    case 'translate':
      return '翻译';
    case 'both':
      return '识别/翻译';
    default:
      return type;
  }
}

export function flattenModelsForType(providers: Provider[], modelType: 'ocr' | 'translate' | 'both'): Array<{
  providerId: number;
  providerName: string;
  modelId: string;
  displayName: string;
}> {
  const result: Array<{
    providerId: number;
    providerName: string;
    modelId: string;
    displayName: string;
  }> = [];
  
  for (const provider of providers) {
    if (provider.is_active !== 'true') continue;
    for (const model of provider.models) {
      if (model.is_active !== 'true') continue;
      if (model.model_type === modelType || model.model_type === 'both') {
        result.push({
          providerId: provider.id,
          providerName: provider.display_name,
          modelId: model.model_id,
          displayName: `${provider.display_name} / ${model.display_name}`,
        });
      }
    }
  }
  
  return result;
}

export interface LanguagePrompt {
  id: number;
  language_code: string;
  language_name: string;
  ocr_prompt: string | null;
  translate_prompt: string | null;
}

export async function getLanguages(): Promise<LanguagePrompt[]> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);
  try {
    const res = await fetch(`${API_BASE}/prompts`, { 
      signal: controller.signal 
    });
    return res.json();
  } finally {
    clearTimeout(timeout);
  }
}