'use client';

import { useState, useEffect } from 'react';
import { getConfig, updateConfig } from '@/lib/api';

export default function SettingsPage() {
  const [modelEndpoint, setModelEndpoint] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const config = await getConfig();
      setModelEndpoint(config.model_endpoint || '');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load config');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      await updateConfig({ model_endpoint: modelEndpoint });
      setSuccess('配置保存成功！');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save config');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-8">
      <div className="max-w-2xl mx-auto px-4">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">
          设置
        </h1>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {success && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-green-800">{success}</p>
          </div>
        )}

        <div className="bg-white shadow rounded-lg p-6">
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Ollama 模型端点
              </label>
              <input
                type="text"
                value={modelEndpoint}
                onChange={(e) => setModelEndpoint(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="http://localhost:11434"
              />
              <p className="mt-2 text-sm text-gray-500">
                例如: http://172.25.249.29:30000
              </p>
            </div>

            <div className="flex gap-4">
              <button
                onClick={handleSave}
                disabled={saving}
                className={`
                  px-6 py-2 bg-blue-600 text-white rounded-md
                  ${saving ? 'opacity-50 cursor-not-allowed' : 'hover:bg-blue-700'}
                `}
              >
                {saving ? '保存中...' : '保存配置'}
              </button>
            </div>
          </div>
        </div>

        <div className="mt-6">
          <button
            onClick={() => window.history.back()}
            className="text-blue-600 hover:text-blue-800"
          >
            ← 返回
          </button>
        </div>
      </div>
    </div>
  );
}
