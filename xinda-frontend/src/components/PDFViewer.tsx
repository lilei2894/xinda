'use client';

import { useState, useEffect, useRef } from 'react';

interface PDFViewerProps {
  fileUrl: string;
  currentPage: number;
  onPageChange: (page: number) => void;
  scale?: number;
}

export default function PDFViewer({ fileUrl, currentPage, onPageChange, scale = 1.0 }: PDFViewerProps) {
  const [error, setError] = useState<string | null>(null);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    const iframe = iframeRef.current;
    if (!iframe) return;
    
    const handleLoad = () => console.log('PDF loaded');
    iframe.addEventListener('load', handleLoad);
    return () => iframe.removeEventListener('load', handleLoad);
  }, []);

  const pdfUrl = `${fileUrl}#page=${currentPage}`;

  return (
    <div className="w-full h-full flex flex-col">
      <div className="flex-1 bg-gray-200 overflow-hidden">
        {error ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center p-8">
              <p className="text-red-600 mb-4">加载失败: {error}</p>
              <a
                href={fileUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                点击在新窗口打开
              </a>
            </div>
          </div>
        ) : (
          <iframe
            ref={iframeRef}
            src={pdfUrl}
            className="w-full h-full border-0"
            style={{ transform: `scale(${scale})`, transformOrigin: 'top left' }}
            onError={() => setError('PDF 加载失败')}
          />
        )}
      </div>
    </div>
  );
}