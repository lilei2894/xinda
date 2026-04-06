'use client';

import { useState } from 'react';
import { exportOcrResult, exportTranslateResult } from '@/lib/api';

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  recordId: string;
  filename: string;
}

export default function ExportModal({ isOpen, onClose, recordId, filename }: ExportModalProps) {
  const [exporting, setExporting] = useState<string | null>(null);

  if (!isOpen) return null;

  const baseName = filename?.replace(/\.[^.]+$/, '') || 'document';

  const handleExport = async (type: 'ocr' | 'translate') => {
    setExporting(type);
    try {
      const blob = type === 'ocr' ? await exportOcrResult(recordId) : await exportTranslateResult(recordId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = type === 'ocr' ? `${baseName}_识别稿.docx` : `${baseName}_翻译稿.docx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      onClose();
    } catch (err) {
      console.error('Export failed:', err);
    } finally {
      setExporting(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-sm overflow-hidden flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">结果导出</h2>
          <button
            onClick={onClose}
            className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="px-6 py-6 space-y-3">
          <button
            onClick={() => handleExport('ocr')}
            disabled={exporting !== null}
            className="w-full flex items-center gap-3 p-4 border border-gray-200 rounded-xl hover:border-emerald-300 hover:bg-emerald-50 transition-colors disabled:opacity-50 group"
          >
            <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center group-hover:bg-emerald-200 transition-colors">
              <svg className="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div className="text-left">
              <div className="text-sm font-medium text-gray-900">导出外文识别稿</div>
              <div className="text-xs text-gray-500">包含原始外文文本识别结果</div>
            </div>
            {exporting === 'ocr' && (
              <svg className="w-5 h-5 text-emerald-600 animate-spin ml-auto" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            )}
          </button>

          <button
            onClick={() => handleExport('translate')}
            disabled={exporting !== null}
            className="w-full flex items-center gap-3 p-4 border border-gray-200 rounded-xl hover:border-blue-300 hover:bg-blue-50 transition-colors disabled:opacity-50 group"
          >
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center group-hover:bg-blue-200 transition-colors">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
              </svg>
            </div>
            <div className="text-left">
              <div className="text-sm font-medium text-gray-900">导出中文翻译稿</div>
              <div className="text-xs text-gray-500">包含翻译后的中文文本</div>
            </div>
            {exporting === 'translate' && (
              <svg className="w-5 h-5 text-blue-600 animate-spin ml-auto" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
