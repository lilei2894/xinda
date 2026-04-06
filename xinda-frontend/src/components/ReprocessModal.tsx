'use client';

import { useState, useEffect } from 'react';
import { getProviders, resetProcessing, continueProcessing } from '@/lib/api';
import type { Provider } from '@/lib/providers';
import { flattenModelsForType } from '@/lib/providers';

interface ReprocessModalProps {
  isOpen: boolean;
  onClose: () => void;
  recordId: string;
  onSuccess: () => void;
  initialOcrModel?: string;
  initialTransModel?: string;
}

export default function ReprocessModal({ isOpen, onClose, recordId, onSuccess, initialOcrModel, initialTransModel }: ReprocessModalProps) {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState<'reset' | 'continue'>('reset');
  const [ocrModel, setOcrModel] = useState('');
  const [transModel, setTransModel] = useState('');
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      getProviders().then(data => {
        setProviders(data);
        const models = flattenModelsForType(data, 'both');
        if (models.length > 0) {
          setOcrModel(initialOcrModel || `${models[0].providerId}/${models[0].modelId}`);
          setTransModel(initialTransModel || `${models[0].providerId}/${models[0].modelId}`);
        }
      }).catch(console.error).finally(() => setLoading(false));
    }
  }, [isOpen]);

  const handleReset = async () => {
    setProcessing(true);
    try {
      const [ocrP, ocrM] = ocrModel.split('/');
      const [transP, transM] = transModel.split('/');
      const ocrProvider = providers.find(p => p.id === parseInt(ocrP));
      await fetch(`http://localhost:8000/api/result/${recordId}/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ocr_model_id: ocrModel,
          translate_model_id: transModel,
          endpoint: ocrProvider?.base_url || '',
          doc_language: 'auto'
        })
      });
      onSuccess();
      onClose();
    } catch (err) {
      console.error('Reset failed:', err);
    } finally {
      setProcessing(false);
    }
  };

  const handleContinue = async () => {
    if (!ocrModel || !transModel) return;
    setProcessing(true);
    try {
      const [ocrP, ocrM] = ocrModel.split('/');
      const [transP, transM] = transModel.split('/');
      const ocrProvider = providers.find(p => p.id === parseInt(ocrP));
      const transProvider = providers.find(p => p.id === parseInt(transP));
      await continueProcessing(
        recordId,
        ocrModel,
        transModel,
        ocrProvider?.base_url || '',
        'ja'
      );
      onSuccess();
      onClose();
    } catch (err) {
      console.error('Continue failed:', err);
    } finally {
      setProcessing(false);
    }
  };

  if (!isOpen) return null;

  const models = flattenModelsForType(providers, 'both');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">重新处理</h2>
          <button
            onClick={onClose}
            className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="px-6 py-4">
          {loading ? (
            <div className="text-center py-8 text-gray-500">加载中...</div>
          ) : (
            <div className="space-y-4">
              <div className="flex gap-2">
                <button
                  onClick={() => setMode('reset')}
                  className={`flex-1 py-2.5 text-sm font-medium rounded-lg transition-colors ${
                    mode === 'reset'
                      ? 'bg-amber-500 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  清空重新开始
                </button>
                <button
                  onClick={() => setMode('continue')}
                  className={`flex-1 py-2.5 text-sm font-medium rounded-lg transition-colors ${
                    mode === 'continue'
                      ? 'bg-amber-500 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  继续未完成处理
                </button>
              </div>

              {mode === 'continue' && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">识别模型</label>
                    <select
                      value={ocrModel}
                      onChange={(e) => setOcrModel(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-500 text-sm text-gray-900"
                    >
                      {models.map((m) => (
                        <option key={`${m.providerId}/${m.modelId}`} value={`${m.providerId}/${m.modelId}`}>
                          {m.displayName}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">翻译模型</label>
                    <select
                      value={transModel}
                      onChange={(e) => setTransModel(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-500 text-sm text-gray-900"
                    >
                      {models.map((m) => (
                        <option key={`${m.providerId}/${m.modelId}`} value={`${m.providerId}/${m.modelId}`}>
                          {m.displayName}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              )}

              {mode === 'reset' && (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                  <p className="text-sm text-amber-800">
                    这将清空当前所有识别和翻译内容，从头开始处理。
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors"
          >
            取消
          </button>
          <button
            onClick={mode === 'reset' ? handleReset : handleContinue}
            disabled={processing}
            className="px-4 py-2 text-sm bg-amber-500 text-white rounded-md hover:bg-amber-600 disabled:opacity-50 transition-colors"
          >
            {processing ? '处理中...' : mode === 'reset' ? '清空重新开始' : '继续处理'}
          </button>
        </div>
      </div>
    </div>
  );
}
