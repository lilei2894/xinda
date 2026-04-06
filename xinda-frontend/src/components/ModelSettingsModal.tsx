'use client';

import { useState, useEffect, type ReactNode } from 'react';
import { getProviders, createProvider, deleteProvider, updateProviderModels, toggleModel, fetchModelsFromProvider } from '@/lib/api';
import type { Provider, ModelEntry } from '@/lib/providers';

interface ModelSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onModelsChange?: () => void;
}

interface ModelRowState {
  id?: number;
  model_id: string;
  display_name: string;
  model_type: string;
  is_default: string;
  is_active: string;
}

const ProviderIcon = ({ name, className = '' }: { name: string; className?: string }) => {
  const icons: Record<string, ReactNode> = {
    ollama: (
      <svg viewBox="0 0 24 24" className={className} fill="currentColor">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
      </svg>
    ),
    openai: (
      <svg viewBox="0 0 24 24" className={className} fill="currentColor">
        <path d="M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5145 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4751 4.4751 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4703 4.4703 0 0 1-.5346-3.03l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.504 4.504 0 0 1-6.1408-1.6464zM2.3392 8.1648a4.4846 4.4846 0 0 1 2.3656-1.9638V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071-.0047L3.9693 13.989a4.5087 4.5087 0 0 1-1.6301-5.8242zM19.3 13.7057l-5.8191-3.3637 2.0201-1.1685a.0757.0757 0 0 1 .071.0047l4.8498 2.8053a4.4945 4.4945 0 0 1-.6385 8.0819 4.4703 4.4703 0 0 1-2.4799-.1277V14.34a.79.79 0 0 0-.3927-.6813l-5.8144-3.3543 2.0201-1.1685a.0757.0757 0 0 1 .071.0047l4.8498 2.8053a4.504 4.504 0 0 1 1.6301 5.8242 4.4703 4.4703 0 0 1-2.3656 1.9638z"/>
      </svg>
    ),
    anthropic: (
      <svg viewBox="0 0 24 24" className={className} fill="currentColor">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
      </svg>
    ),
    google: (
      <svg viewBox="0 0 24 24" className={className} fill="currentColor">
        <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
        <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
        <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
        <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
      </svg>
    ),
  };

  return icons[name.toLowerCase()] || (
    <svg viewBox="0 0 24 24" className={className} fill="currentColor">
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
    </svg>
  );
};

export default function ModelSettingsModal({ isOpen, onClose, onModelsChange }: ModelSettingsModalProps) {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedProviders, setExpandedProviders] = useState<Set<string>>(new Set());
  const [showCustomForm, setShowCustomForm] = useState(false);
  const [editingProvider, setEditingProvider] = useState<Provider | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [hasChanges, setHasChanges] = useState(false);

  const filteredProviders = providers.filter(provider => {
    const query = searchQuery.toLowerCase();
    const providerMatch = provider.name.toLowerCase().includes(query) || 
      provider.display_name.toLowerCase().includes(query);
    const modelMatch = provider.models.some(model => 
      model.model_id.toLowerCase().includes(query) || 
      model.display_name.toLowerCase().includes(query)
    );
    return providerMatch || modelMatch;
  });

  const getFilteredModels = (provider: Provider) => {
    if (!searchQuery) return provider.models;
    const query = searchQuery.toLowerCase();
    return provider.models.filter(model => 
      model.model_id.toLowerCase().includes(query) || 
      model.display_name.toLowerCase().includes(query)
    );
  };

  useEffect(() => {
    if (searchQuery && providers.length > 0) {
      const matchingProviders = providers.filter(provider => {
        const query = searchQuery.toLowerCase();
        const providerMatch = provider.name.toLowerCase().includes(query) || 
          provider.display_name.toLowerCase().includes(query);
        const modelMatch = provider.models.some(model => 
          model.model_id.toLowerCase().includes(query) || 
          model.display_name.toLowerCase().includes(query)
        );
        return providerMatch || modelMatch;
      });
      setExpandedProviders(new Set(matchingProviders.map(p => p.name)));
    }
  }, [searchQuery]);

  const [formProviderId, setFormProviderId] = useState('');
  const [formName, setFormName] = useState('');
  const [formBaseUrl, setFormBaseUrl] = useState('');
  const [formApiKey, setFormApiKey] = useState('');
  const [formModels, setFormModels] = useState<ModelRowState[]>([{ model_id: '', display_name: '', model_type: 'both', is_default: 'false', is_active: 'true' }]);
  const [adding, setAdding] = useState(false);
  const [fetchingModels, setFetchingModels] = useState(false);

  const loadProviders = async () => {
    try {
      const data = await getProviders();
      setProviders(data);
    } catch (err) {
      console.error('Failed to load providers:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadProviders();
      setHasChanges(false);
    }
  }, [isOpen]);

  const handleClose = () => {
    setSearchQuery('');
    if (hasChanges) {
      onModelsChange?.();
    }
    onClose();
  };

  const addModelRow = () => {
    setFormModels(prev => [...prev, { model_id: '', display_name: '', model_type: 'both', is_default: 'false', is_active: 'true' }]);
  };

  const removeModelRow = (index: number) => {
    if (formModels.length <= 1) return;
    setFormModels(prev => prev.filter((_, i) => i !== index));
  };

  const updateModelRow = (index: number, key: string, value: string) => {
    setFormModels(prev => prev.map((row, i) => i === index ? { ...row, [key]: value } : row));
  };

  const handleAddProvider = async () => {
    if (!formProviderId || !formName || !formBaseUrl) return;

    setAdding(true);
    try {
      const validModels = formModels.filter(m => m.model_id.trim() && m.display_name.trim());
      await createProvider({
        name: formProviderId,
        display_name: formName,
        base_url: formBaseUrl,
        api_key: formApiKey || undefined,
        models: validModels.map(m => ({ id: m.model_id, name: m.display_name })),
      });
      setHasChanges(true);
      resetForm();
      await loadProviders();
    } catch (err: any) {
      console.error('Failed to add provider:', err);
    } finally {
      setAdding(false);
    }
  };

  const handleDeleteProvider = async (id: number) => {
    if (!confirm('确定要删除这个提供商吗？')) return;
    try {
      await deleteProvider(id);
      setHasChanges(true);
      await loadProviders();
    } catch (err) {
      console.error('Failed to delete provider:', err);
    }
  };

  const handleToggleModel = async (modelId: number, currentActive: string) => {
    const newActive = currentActive === 'true' ? 'false' : 'true';
    try {
      await toggleModel(modelId, newActive);
      setHasChanges(true);
      await loadProviders();
    } catch (err) {
      console.error('Failed to toggle model:', err);
    }
  };

  const handleFetchModels = async () => {
    if (!formBaseUrl) return;
    setFetchingModels(true);
    try {
      const result = await fetchModelsFromProvider({
        base_url: formBaseUrl,
        api_key: formApiKey || undefined,
        name: formProviderId,
      });
      if (result.models && result.models.length > 0) {
        setFormModels(result.models);
      } else {
        alert('未找到模型列表，请检查 API 地址和密钥是否正确');
      }
    } catch (err) {
      console.error('Failed to fetch models:', err);
      alert('获取模型列表失败，请检查网络连接');
    } finally {
      setFetchingModels(false);
    }
  };

  const toggleProviderExpand = (name: string) => {
    setExpandedProviders(prev => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  };

  const handleStartEdit = (provider: Provider) => {
    setEditingProvider(provider);
    setFormProviderId(provider.name);
    setFormName(provider.display_name);
    setFormBaseUrl(provider.base_url);
    setFormApiKey('');
    setFormModels(provider.models.map(m => ({
      id: m.id,
      model_id: m.model_id,
      display_name: m.display_name,
      model_type: m.model_type,
      is_default: m.is_default,
      is_active: m.is_active,
    })));
    setShowCustomForm(true);
  };

  const handleCancelEdit = () => {
    setEditingProvider(null);
    resetForm();
  };

  const handleSaveEdit = async () => {
    if (!editingProvider) return;

    setAdding(true);
    try {
      const validModels = formModels.filter(m => m.model_id.trim() && m.display_name.trim());
      await updateProviderModels(editingProvider.id, {
        display_name: formName,
        base_url: formBaseUrl,
        api_key: formApiKey || undefined,
        models: validModels.map(m => ({
          model_id: m.model_id,
          display_name: m.display_name,
          model_type: m.model_type,
          is_default: m.is_default,
          is_active: m.is_active,
        })),
      });
      setHasChanges(true);
      setEditingProvider(null);
      resetForm();
      await loadProviders();
    } catch (err: any) {
      console.error('Failed to update provider:', err);
    } finally {
      setAdding(false);
    }
  };

  const resetForm = () => {
    setFormProviderId('');
    setFormName('');
    setFormBaseUrl('');
    setFormApiKey('');
    setFormModels([{ model_id: '', display_name: '', model_type: 'both', is_default: 'false', is_active: 'true' }]);
    setShowCustomForm(false);
    setEditingProvider(null);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" onClick={handleClose} />

      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[85vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">模型设置</h2>
          <button
            onClick={handleClose}
            className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="px-6 py-3 border-b border-gray-200">
          <div className="relative">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="搜索提供商或模型..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm text-gray-900 placeholder-gray-900"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>

        <div className="overflow-y-auto flex-1">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <span className="text-sm text-gray-500">加载中...</span>
            </div>
          ) : (
            <div className="px-6 py-4">
              <div className="space-y-6">
                {filteredProviders.map((provider) => {
                  const isExpanded = expandedProviders.has(provider.name);
                  const isPreset = ['ollama', 'openai', 'anthropic', 'google'].includes(provider.name);

                  return (
                    <div key={provider.id} className="space-y-2">
                      <div
                        className="flex items-center justify-between py-3 px-3 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer"
                        onClick={() => toggleProviderExpand(provider.name)}
                      >
                        <div className="flex items-center gap-3">
                          {isPreset && (
                            <ProviderIcon name={provider.name} className="w-5 h-5 text-gray-700 flex-shrink-0" />
                          )}
                          <span className="text-sm font-medium text-gray-900">{provider.display_name}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <svg className="w-4 h-4 text-green-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleProviderExpand(provider.name);
                            }}
                            className="text-blue-600 hover:text-blue-800 p-1.5 rounded hover:bg-blue-50 transition-colors"
                            title={isExpanded ? '收起' : '查看模型'}
                          >
                            {isExpanded ? (
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L6.59 6.59m7.532 7.532l3.29 3.29M3 3l18 18" />
                              </svg>
                            ) : (
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                              </svg>
                            )}
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleStartEdit(provider);
                            }}
                            className="text-sm text-blue-600 hover:text-blue-800 px-1.5 py-1 rounded hover:bg-blue-50 transition-colors"
                            title="编辑"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                          </button>
                          {!isPreset && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteProvider(provider.id);
                              }}
                              className="text-red-500 hover:text-red-700 px-1.5 py-1 rounded hover:bg-red-50 transition-colors"
                              title="删除提供商"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            </button>
                          )}
                        </div>
                      </div>

                      {isExpanded && provider.models.length > 0 && getFilteredModels(provider).length === 0 && (
                        <div className="bg-gray-50 rounded-lg px-4 py-4 text-center">
                          <span className="text-sm text-gray-500">该提供商下没有匹配模型</span>
                        </div>
                      )}

                      {isExpanded && provider.models.length > 0 && getFilteredModels(provider).length > 0 && (
                        <div className="bg-gray-50 rounded-lg px-4">
                          {getFilteredModels(provider).map((model, idx) => (
                            <div
                              key={model.id}
                              className={`flex items-center justify-between py-3 ${
                                idx !== getFilteredModels(provider).length - 1 ? 'border-b border-gray-200' : ''
                              }`}
                            >
                              <div className="min-w-0 flex-1">
                                <span className={`text-sm truncate block ${model.is_active === 'true' ? 'text-gray-900' : 'text-gray-400 line-through'}`}>{model.display_name}</span>
                                <span className="text-xs text-gray-500">{model.model_id}</span>
                              </div>
                              <div className="flex-shrink-0 flex items-center gap-2">
                                {model.is_default === 'true' && (
                                  <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">默认</span>
                                )}
                                <label className="relative inline-flex items-center cursor-pointer">
                                  <input
                                    type="checkbox"
                                    checked={model.is_active === 'true'}
                                    onChange={() => model.id && handleToggleModel(model.id, model.is_active)}
                                    className="sr-only peer"
                                  />
                                  <div className="w-9 h-5 bg-gray-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                                </label>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      {isExpanded && provider.models.length === 0 && (
                        <div className="bg-gray-50 rounded-lg px-4 py-6 text-center">
                          <span className="text-sm text-gray-500">暂无模型</span>
                        </div>
                      )}
                    </div>
                  );
                })}

                {filteredProviders.length === 0 && !showCustomForm && (
                  <div className="flex flex-col items-center justify-center py-12 text-center">
                    {searchQuery ? (
                      <>
                        <span className="text-sm text-gray-500">未找到匹配的结果</span>
                        <span className="text-xs text-gray-400 mt-1">试试其他搜索词</span>
                      </>
                    ) : (
                      <>
                        <span className="text-sm text-gray-500">暂无提供商</span>
                        <span className="text-xs text-gray-400 mt-1">点击下方按钮添加</span>
                      </>
                    )}
                  </div>
                )}

                <div>
                  {!showCustomForm ? (
                    <button
                      onClick={() => setShowCustomForm(true)}
                      className="flex items-center gap-2 w-full py-3 px-3 rounded-lg hover:bg-gray-50 transition-colors text-sm text-gray-600 hover:text-gray-900"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                      添加提供商与模型
                    </button>
                  ) : (
                    <div className="space-y-4">
                      <div className="flex items-center gap-3 px-3 py-2">
                        <span className="text-sm font-medium text-gray-900">{editingProvider ? '编辑提供商与模型' : '添加提供商与模型'}</span>
                      </div>

                      <div className="bg-gray-50 rounded-lg px-4 py-3 space-y-3">
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">提供商 ID</label>
                          <input
                            type="text"
                            value={formProviderId}
                            onChange={(e) => setFormProviderId(e.target.value)}
                            placeholder="例如：my-provider"
                            disabled={!!editingProvider}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm text-gray-900 placeholder-gray-900 disabled:bg-gray-100 disabled:opacity-70"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">显示名称</label>
                          <input
                            type="text"
                            value={formName}
                            onChange={(e) => setFormName(e.target.value)}
                            placeholder="例如：My Provider"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm text-gray-900 placeholder-gray-900"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">API 地址</label>
                          <input
                            type="text"
                            value={formBaseUrl}
                            onChange={(e) => setFormBaseUrl(e.target.value)}
                            placeholder="例如：https://api.example.com/v1"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm text-gray-900 placeholder-gray-900"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-700 mb-1">API 密钥（可选）</label>
                          <input
                            type="password"
                            value={formApiKey}
                            onChange={(e) => setFormApiKey(e.target.value)}
                            placeholder={editingProvider ? '留空则不修改' : 'sk-...'}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm text-gray-900 placeholder-gray-900"
                          />
                        </div>

                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <label className="block text-xs font-medium text-gray-500">模型</label>
                            <button
                              type="button"
                              onClick={handleFetchModels}
                              disabled={fetchingModels || !formBaseUrl}
                              className="text-xs text-blue-600 hover:text-blue-800 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                            >
                              {fetchingModels ? (
                                <>
                                  <svg className="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                  </svg>
                                  获取中...
                                </>
                              ) : (
                                <>
                                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                  </svg>
                                  获取模型列表
                                </>
                              )}
                            </button>
                          </div>
                          {formModels.map((model, index) => (
                            <div key={index} className="flex gap-2 items-start">
                              <div className="flex-1">
                                <input
                                  type="text"
                                  value={model.model_id}
                                  onChange={(e) => updateModelRow(index, 'model_id', e.target.value)}
                                  placeholder="模型 ID"
                                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm text-gray-900 placeholder-gray-900"
                                />
                              </div>
                              <div className="flex-1">
                                <input
                                  type="text"
                                  value={model.display_name}
                                  onChange={(e) => updateModelRow(index, 'display_name', e.target.value)}
                                  placeholder="显示名称"
                                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm text-gray-900 placeholder-gray-900"
                                />
                              </div>
                              <button
                                type="button"
                                onClick={() => removeModelRow(index)}
                                disabled={formModels.length <= 1}
                                className="p-2 mt-0.5 text-gray-400 hover:text-red-500 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                              </button>
                            </div>
                          ))}
                          <button
                            type="button"
                            onClick={addModelRow}
                            className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900 transition-colors"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                            </svg>
                            添加模型
                          </button>
                        </div>

                        <div className="flex gap-2 justify-end pt-2">
                          <button
                            onClick={editingProvider ? handleCancelEdit : resetForm}
                            className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors"
                          >
                            取消
                          </button>
                          <button
                            onClick={editingProvider ? handleSaveEdit : handleAddProvider}
                            disabled={adding || !formProviderId || !formName || !formBaseUrl}
                            className="px-3 py-1.5 text-sm bg-gray-900 text-white rounded-md hover:bg-gray-800 disabled:opacity-50 transition-colors"
                          >
                            {adding ? '保存中...' : (editingProvider ? '保存' : '添加')}
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}