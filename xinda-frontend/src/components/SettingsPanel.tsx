'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { usePathname } from 'next/navigation';
import { getExtendedConfig, updateExtendedConfig, getProviders } from '@/lib/api';
import type { Provider } from '@/lib/providers';
import { flattenModelsForType, getLanguages, type LanguagePrompt } from '@/lib/providers';
import CustomDropdown from './CustomDropdown';

interface SettingsPanelProps {
  onOpenModelSettings: () => void;
  onOpenPromptSettings: () => void;
  onStartProcessing?: (ocrModel: string, translateModel: string, endpoint: string, docLanguage: string) => void;
}

interface SettingsPanelState {
  model_endpoint: string;
  doc_language: string;
  ocr_model_id?: string | null;
  translate_model_id?: string | null;
}

export default function SettingsPanel({ onOpenModelSettings, onOpenPromptSettings, onStartProcessing }: SettingsPanelProps) {
  const pathname = usePathname();
  const [config, setConfig] = useState<SettingsPanelState | null>(null);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [languages, setLanguages] = useState<LanguagePrompt[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = () => setRefreshKey(k => k + 1);
    window.addEventListener('refresh-home-data', handler);
    return () => window.removeEventListener('refresh-home-data', handler);
  }, []);

  const loadData = useCallback(async () => {
    try {
      const [configData, providersData, languagesData] = await Promise.all([
        getExtendedConfig(),
        getProviders(),
        getLanguages(),
      ]);
      setConfig(configData);
      setProviders(providersData);
      setLanguages(languagesData);
    } catch (err) {
      console.error('Failed to load settings:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData, refreshKey, pathname]);

  const handleDocLanguageChange = async (value: string) => {
    if (!config) return;
    setSaving(true);
    try {
      await updateExtendedConfig({ doc_language: value });
      setConfig({ ...config, doc_language: value });
    } catch (err) {
      console.error('Failed to update doc_language:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleOcrModelChange = async (value: string) => {
    if (!config) return;
    setSaving(true);
    try {
      await updateExtendedConfig({ ocr_model_id: value || null });
      setConfig({ ...config, ocr_model_id: value || null });
    } catch (err) {
      console.error('Failed to update ocr_model_id:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleTranslateModelChange = async (value: string) => {
    if (!config) return;
    setSaving(true);
    try {
      await updateExtendedConfig({ translate_model_id: value || null });
      setConfig({ ...config, translate_model_id: value || null });
    } catch (err) {
      console.error('Failed to update translate_model_id:', err);
    } finally {
      setSaving(false);
    }
  };

  const resolveModelConfig = (compoundValue: string): { modelName: string; endpoint: string } => {
    if (!compoundValue) return { modelName: '', endpoint: '' };
    const [providerIdStr, modelId] = compoundValue.split('/');
    const providerId = parseInt(providerIdStr, 10);
    const provider = providers.find(p => p.id === providerId);
    return {
      modelName: modelId,
      endpoint: provider?.base_url || '',
    };
  };

  const ocrModels = flattenModelsForType(providers, 'both');
  const translateModels = flattenModelsForType(providers, 'both');

  if (loading) {
    return (
      <div ref={panelRef} className="bg-white rounded-lg shadow p-6 flex flex-col" data-testid="settings-panel">
        <div className="animate-pulse space-y-3">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="h-10 bg-gray-200 rounded"></div>
          <div className="h-10 bg-gray-200 rounded"></div>
          <div className="h-10 bg-gray-200 rounded"></div>
        </div>
        <div className="flex-1"></div>
        <div className="h-12 bg-gray-200 rounded mt-4"></div>
      </div>
    );
  }

  return (
    <div ref={panelRef} className="bg-white rounded-lg shadow p-6" data-testid="settings-panel">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">处理设置</h2>
        <div className="flex gap-2">
          <button
            onClick={onOpenModelSettings}
            className="px-3 py-1.5 text-sm text-white rounded-md hover:opacity-80 transition-opacity"
            style={{ backgroundColor: '#8FA3A6' }}
          >
            模型设置
          </button>
          <button
            onClick={onOpenPromptSettings}
            className="px-3 py-1.5 text-sm text-white rounded-md hover:opacity-80 transition-opacity"
            style={{ backgroundColor: '#B5A8B5' }}
          >
            提示词设置
          </button>
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center gap-3">
          <label className="text-base font-medium text-gray-700 w-20 flex-shrink-0">
            文档语言
          </label>
          <CustomDropdown
            value={config?.doc_language || 'auto'}
            onChange={handleDocLanguageChange}
            options={[
              ...(config?.doc_language && config.doc_language !== 'auto' 
                ? [{ value: 'auto', label: `自动检测（${languages.find(l => l.language_code === config.doc_language)?.language_name || config.doc_language.toUpperCase()}）` }]
                : [{ value: 'auto', label: '-- 自动检测 --' }]
              ),
              ...languages.map((lang) => ({
                value: lang.language_code,
                label: lang.language_name
              }))
            ]}
            placeholder="-- 自动检测 --"
            className="flex-1"
            disabled={saving}
          />
        </div>

        <div className="flex items-center gap-3">
          <label className="text-base font-medium text-gray-700 w-20 flex-shrink-0">
            识别模型
          </label>
          <CustomDropdown
            value={config?.ocr_model_id || ''}
            onChange={handleOcrModelChange}
            options={[
              { value: '', label: '-- 选择模型 --' },
              ...ocrModels.map((m) => ({
                value: `${m.providerId}/${m.modelId}`,
                label: m.displayName
              }))
            ]}
            placeholder="-- 选择模型 --"
            className="flex-1"
            disabled={saving}
          />
        </div>

        <div className="flex items-center gap-3">
          <label className="text-base font-medium text-gray-700 w-20 flex-shrink-0">
            翻译模型
          </label>
          <CustomDropdown
            value={config?.translate_model_id || ''}
            onChange={handleTranslateModelChange}
            options={[
              { value: '', label: '-- 选择模型 --' },
              ...translateModels.map((m) => ({
                value: `${m.providerId}/${m.modelId}`,
                label: m.displayName
              }))
            ]}
            placeholder="-- 选择模型 --"
            className="flex-1"
            disabled={saving}
          />
        </div>
      </div>

      {saving && (
        <div className="text-sm text-gray-500 text-center py-1">
          保存中...
        </div>
      )}

      <button
        onClick={() => {
          const ocrRaw = config?.ocr_model_id || '';
          const translateRaw = config?.translate_model_id || '';
          const ocrConfig = resolveModelConfig(ocrRaw);
          const docLanguage = config?.doc_language || 'auto';
          if (onStartProcessing) {
            onStartProcessing(ocrRaw, translateRaw, ocrConfig.endpoint, docLanguage);
          }
        }}
        className="w-full mt-4 py-3 text-white font-medium rounded-lg hover:opacity-80 transition-opacity"
        style={{ backgroundColor: '#A89F91' }}
      >
        开始处理
      </button>
    </div>
  );
}
