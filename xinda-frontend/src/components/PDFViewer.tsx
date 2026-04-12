'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Document, Page } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

interface PDFViewerProps {
  fileUrl: string;
  currentPage: number;
  onPageChange: (page: number) => void;
  scale?: number;
}

export default function PDFViewer({ fileUrl, currentPage, onPageChange, scale = 1.0 }: PDFViewerProps) {
  const [numPages, setNumPages] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerSize, setContainerSize] = useState({ width: 0, height: 0 });
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const panStart = useRef({ x: 0, y: 0 });
  const lastPan = useRef({ x: 0, y: 0 });
  const workerSet = useRef(false);

  useEffect(() => {
    if (!workerSet.current && typeof window !== 'undefined') {
      import('pdfjs-dist').then((pdfjs) => {
        pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';
        workerSet.current = true;
      }).catch(console.error);
    }
  }, []);

  function onDocumentLoadSuccess({ numPages: pages }: { numPages: number }) {
    setNumPages(pages);
  }

  function onDocumentLoadError(err: Error) {
    setError(err.message);
  }

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

  useEffect(() => {
    if (scale <= 0) {
      setPan({ x: 0, y: 0 });
      lastPan.current = { x: 0, y: 0 };
    }
  }, [scale]);

  const autoScale = containerSize.width > 0 && containerSize.height > 0 ? Math.min(
    (containerSize.width - 20) / 500,
    (containerSize.height - 20) / 700
  ) : 1.0;

  const effectiveScale = scale <= 0 ? autoScale : scale;

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleWheelNative = (e: WheelEvent) => {
      e.preventDefault();
      e.stopPropagation();
      const delta = e.deltaY > 0 ? -0.1 : 0.1;
      const newScale = Math.max(0.3, Math.min(5.0, effectiveScale + delta));
      window.dispatchEvent(new CustomEvent('pdf-scale-change', { detail: { scale: newScale } }));
    };

    container.addEventListener('wheel', handleWheelNative, { passive: false });
    return () => {
      container.removeEventListener('wheel', handleWheelNative);
    };
  }, [effectiveScale]);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsPanning(true);
    panStart.current = { x: e.clientX - lastPan.current.x, y: e.clientY - lastPan.current.y };
  }, []);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isPanning) {
        const newX = e.clientX - panStart.current.x;
        const newY = e.clientY - panStart.current.y;
        setPan({ x: newX, y: newY });
        lastPan.current = { x: newX, y: newY };
      }
    };

    const handleMouseUp = () => {
      if (isPanning) {
        setIsPanning(false);
      }
    };

    if (isPanning) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isPanning]);

  return (
    <div className="w-full h-full flex flex-col">
      <div 
        ref={containerRef} 
        className="flex-1 overflow-hidden bg-gray-200"
        onMouseDown={handleMouseDown}
        style={{ cursor: isPanning ? 'grabbing' : 'grab' }}
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
          <div 
            className="flex items-center justify-center"
            style={{ 
              width: Math.max(containerSize.width, 500 * effectiveScale), 
              height: Math.max(containerSize.height, 700 * effectiveScale),
              padding: '8px'
            }}
          >
            <Document
              file={fileUrl}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={onDocumentLoadError}
              loading={
                <div className="flex items-center justify-center h-64">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                </div>
              }
              error={
                <div className="flex items-center justify-center h-64">
                  <p className="text-red-600">加载失败</p>
                </div>
              }
            >
              <div
                style={{
                  transform: `translate(${pan.x}px, ${pan.y}px) scale(${effectiveScale})`,
                  transformOrigin: 'center center',
                  transition: isPanning ? 'none' : 'transform 0.1s ease-out'
                }}
              >
                <Page
                  pageNumber={currentPage}
                  scale={1}
                  className="shadow-lg"
                  renderTextLayer={false}
                  renderAnnotationLayer={false}
                />
              </div>
            </Document>
          </div>
        )}
      </div>
    </div>
  );
}