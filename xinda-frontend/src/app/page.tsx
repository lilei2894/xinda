'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import FileUpload from '@/components/FileUpload';
import HistoryList from '@/components/HistoryList';
import SettingsPanel from '@/components/SettingsPanel';
import ModelSettingsModal from '@/components/ModelSettingsModal';
import PromptSettingsModal from '@/components/PromptSettingsModal';
import DonationModal from '@/components/DonationModal';

export default function Home() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [showModelModal, setShowModelModal] = useState(false);
  const [showPromptModal, setShowPromptModal] = useState(false);
  const [showDonationModal, setShowDonationModal] = useState(false);
  const [uploadedFileId, setUploadedFileId] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleUploadSuccess = useCallback((id: string) => {
    setUploadedFileId(id);
    setIsUploading(false);
  }, []);

  const handleUploadError = useCallback((errorMessage: string) => {
    setError(errorMessage);
    setIsUploading(false);
    setTimeout(() => setError(null), 5000);
  }, []);

  const handleStartProcessing = useCallback((ocrModel: string, translateModel: string, endpoint: string, docLanguage: string) => {
    if (!uploadedFileId) {
      setError('请先上传文件');
      setTimeout(() => setError(null), 3000);
      return;
    }

    if (!ocrModel || !translateModel) {
      setError('请选择识别模型和翻译模型');
      setTimeout(() => setError(null), 3000);
      return;
    }

    // Start processing in background (don't wait for response)
    fetch(
      `http://localhost:8000/api/upload/${uploadedFileId}/process?ocr_model=${encodeURIComponent(ocrModel)}&translate_model=${encodeURIComponent(translateModel)}&endpoint=${encodeURIComponent(endpoint)}&language=${encodeURIComponent(docLanguage)}`,
      { method: 'POST' }
    ).catch(err => {
      console.error('Failed to start processing:', err);
    });

    // Navigate immediately
    router.push(`/result/${uploadedFileId}`);
  }, [uploadedFileId, router]);

  return (
    <main className="min-h-screen py-12">
      <div className="max-w-6xl mx-auto px-4">
        <div className="relative mb-8">
          <h1 className="text-4xl font-bold text-gray-900 text-center flex items-center justify-center gap-3">
            <img src="/logo.png" alt="Logo" className="h-10 w-auto" />
            外文档案文献处理工作台
          </h1>
          <a
            href="/usage"
            target="_blank"
            rel="noopener noreferrer"
            className="absolute right-0 bottom-0 text-sm text-blue-600 hover:text-blue-800 underline"
          >
            使用指南
          </a>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        <div className="flex flex-col lg:flex-row gap-6 mb-8">
          <div className="w-full lg:w-[60%]">
            <FileUpload
              isUploading={isUploading}
              onUploadSuccess={handleUploadSuccess}
              onUploadError={handleUploadError}
            />
          </div>
          <div className="w-full lg:w-[40%]">
            <SettingsPanel 
              onOpenModelSettings={() => setShowModelModal(true)}
              onOpenPromptSettings={() => setShowPromptModal(true)}
              onStartProcessing={handleStartProcessing}
            />
          </div>
        </div>

        <HistoryList />

        <ModelSettingsModal
          isOpen={showModelModal}
          onClose={() => setShowModelModal(false)}
        />

        <PromptSettingsModal
          isOpen={showPromptModal}
          onClose={() => setShowPromptModal(false)}
          onPromptsChange={() => {
            window.dispatchEvent(new Event('refresh-home-data'));
          }}
        />
      </div>

      <div className="mt-16 text-center text-sm text-gray-400">
        信达 XINDA © 2026 Pedro ·{' '}
        <a
          href="https://github.com/lilei2894/信达"
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:text-blue-800 underline"
        >
          GitHub
        </a>{' '}
        ·{' '}
        <button
          onClick={() => setShowDonationModal(true)}
          className="text-blue-600 hover:text-blue-800 underline"
        >
          捐赠 ☕
        </button>
      </div>

      <DonationModal
        isOpen={showDonationModal}
        onClose={() => setShowDonationModal(false)}
      />
    </main>
  );
}
