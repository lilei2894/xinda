'use client';

import { useState, useEffect, useRef } from 'react';

interface PDFViewerProps {
  fileUrl: string;
  currentPage: number;
  onPageChange: (page: number) => void;
  scale?: number;
}

function Loading-spinner() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  );
}

export default function PDFViewer({ fileUrl, currentPage, onPageChange, scale = 1.0 }: PDFViewerProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerSize, setContainerSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    
    const updateSize = () => {
      setContainerSize({ width: container.clientWidth, height: container.clientHeight });
    };
    
    updateSize();
    const resizeObserver = new ResizeObserver(updateSize);
    resizeObserver.observe(container);
    return () => resizeObserver.disconnect();
  }, []);

  const effectiveScale = scale <= 0 ? 1.0 : scale;

  return (
    <div className="w-full h-full flex flex-col">
      <div 
        ref={containerRef} 
        className="flex-1 bg-gray-200 overflow-hidden"
      >
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
            src={`${fileUrl}#page=${currentPage}`}
            className="w-full h-full border-0"
            style={{ transform: `scale(${effectiveScale})`, transformOrigin: 'top left' }}
            onLoad={() => setLoading(false)}
            onError={() => setError('PDF 加载失败')}
          />
        )}
      </div>
    </div>
  );
}