'use client';

import { useState, useEffect } from 'react';

interface LanguagePrompt {
  id: number;
  language_code: string;
  language_name: string;
  ocr_prompt: string | null;
  translate_prompt: string | null;
}

interface PromptSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onPromptsChange?: () => void;
}

const API_BASE = 'http://localhost:8000/api';

type SubTab = 'ocr' | 'translate';

export default function PromptSettingsModal({ isOpen, onClose, onPromptsChange }: PromptSettingsModalProps) {
  const [languages, setLanguages] = useState<LanguagePrompt[]>([]);
  const [selectedLanguage, setSelectedLanguage] = useState<string | null>(null);
  const [subTab, setSubTab] = useState<SubTab>('ocr');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newLangCode, setNewLangCode] = useState('');
  const [newLangName, setNewLangName] = useState('');
  const [adding, setAdding] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  const loadLanguages = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/prompts`);
      const data = await res.json();
      setLanguages(data);
      if (data.length > 0 && !selectedLanguage) {
        setSelectedLanguage(data[0].language_code);
      }
    } catch (err) {
      console.error('Failed to load languages:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadLanguages();
      setSaved(false);
    }
  }, [isOpen]);

  const currentLang = languages.find(l => l.language_code === selectedLanguage);

  const getCurrentPrompt = (): string => {
    if (!currentLang) return '';
    return subTab === 'ocr' ? (currentLang.ocr_prompt || '') : (currentLang.translate_prompt || '');
  };

  const updateCurrentPrompt = (value: string) => {
    setLanguages(prev => prev.map(l => {
      if (l.language_code === selectedLanguage) {
        return {
          ...l,
          [subTab === 'ocr' ? 'ocr_prompt' : 'translate_prompt']: value
        };
      }
      return l;
    }));
  };

  const handleSave = async () => {
    if (!currentLang) return;
    setSaving(true);
    try {
      await fetch(`${API_BASE}/prompts/${currentLang.language_code}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ocr_prompt: currentLang.ocr_prompt,
          translate_prompt: currentLang.translate_prompt
        }),
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      console.error('Failed to save prompt:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleAddLanguage = async () => {
    if (!newLangCode.trim() || !newLangName.trim()) return;
    setAdding(true);
    setAddError(null);
    try {
      const res = await fetch(`${API_BASE}/prompts/${newLangCode.trim()}/generate?language_name=${encodeURIComponent(newLangName.trim())}`, {
        method: 'POST'
      });
      if (res.ok) {
        await loadLanguages();
        setSelectedLanguage(newLangCode.trim());
        setShowAddModal(false);
        setNewLangCode('');
        setNewLangName('');
      } else {
        const errData = await res.json();
        setAddError(errData.detail || '添加失败');
      }
    } catch (err) {
      console.error('Failed to add language:', err);
      setAddError('网络错误');
    } finally {
      setAdding(false);
    }
  };

  const handleDeleteLanguage = async (code: string) => {
    if (!confirm('确定删除此语种吗？删除后将无法恢复。')) return;
    setDeleting(code);
    try {
      await fetch(`${API_BASE}/prompts/${code}`, { method: 'DELETE' });
      await loadLanguages();
      if (selectedLanguage === code) {
        setSelectedLanguage(languages[0]?.language_code || null);
      }
    } catch (err) {
      console.error('Failed to delete language:', err);
    } finally {
      setDeleting(null);
    }
  };

  const handleClose = () => {
    onPromptsChange?.();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" onClick={handleClose} />
      
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[85vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">提示词设置</h2>
          <button
            onClick={onClose}
            className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex flex-1 overflow-hidden">
          <div className="w-40 border-r border-gray-200 flex flex-col">
            <div className="flex-1 overflow-y-auto py-2">
              {loading ? (
                <div className="text-center py-4 text-gray-500 text-sm">加载中...</div>
              ) : (
                languages.map(lang => (
                  <div
                    key={lang.language_code}
                    className={`group flex items-center justify-between px-4 py-2 cursor-pointer transition-colors ${
                      selectedLanguage === lang.language_code
                        ? 'bg-blue-50 text-blue-600'
                        : 'hover:bg-gray-50 text-gray-700'
                    }`}
                    onClick={() => setSelectedLanguage(lang.language_code)}
                  >
                    <span className="text-sm font-medium truncate">{lang.language_name}</span>
                    {languages.length > 1 && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteLanguage(lang.language_code);
                        }}
                        disabled={deleting === lang.language_code}
                        className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-opacity disabled:opacity-50"
                        title="删除"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    )}
                  </div>
                ))
              )}
            </div>
            <div className="p-2 border-t border-gray-200">
              <button
                onClick={() => setShowAddModal(true)}
                className="w-full flex items-center justify-center gap-1 px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                新增语种
              </button>
            </div>
          </div>

          <div className="flex-1 flex flex-col">
            {currentLang && (
              <>
                <div className="flex border-b border-gray-200">
                  <button
                    onClick={() => setSubTab('ocr')}
                    className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                      subTab === 'ocr'
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    识别
                  </button>
                  <button
                    onClick={() => setSubTab('translate')}
                    className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                      subTab === 'translate'
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    翻译
                  </button>
                </div>

                <div className="flex-1 overflow-y-auto p-4">
                  <textarea
                    value={getCurrentPrompt()}
                    onChange={(e) => updateCurrentPrompt(e.target.value)}
                    className="w-full h-full min-h-[400px] px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm text-gray-900 placeholder-gray-500 resize-none font-mono leading-relaxed"
                    placeholder={subTab === 'ocr' ? '请输入识别提示词...' : '请输入翻译提示词...'}
                  />
                </div>

                <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200">
                  {saved && (
                    <span className="text-sm text-green-600">已保存</span>
                  )}
                  <button
                    onClick={onClose}
                    className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors"
                  >
                    关闭
                  </button>
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="px-4 py-2 text-sm bg-gray-900 text-white rounded-md hover:bg-gray-800 disabled:opacity-50 transition-colors"
                  >
                    {saving ? '保存中...' : '保存'}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {showAddModal && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center">
          <div className="fixed inset-0 bg-black/50" onClick={() => setShowAddModal(false)} />
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">新增语种</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">语种代码</label>
                <input
                  type="text"
                  value={newLangCode}
                  onChange={(e) => setNewLangCode(e.target.value.toLowerCase())}
                  placeholder="如：ko, fr, de"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">语种名称</label>
                <input
                  type="text"
                  value={newLangName}
                  onChange={(e) => setNewLangName(e.target.value)}
                  placeholder="如：韩语, Français, Deutsch"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                />
              </div>
            </div>
            {addError && (
              <div className="text-sm text-red-600 mt-2">{addError}</div>
            )}
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleAddLanguage}
                disabled={adding || !newLangCode.trim() || !newLangName.trim()}
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {adding ? '添加中...' : '添加'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
