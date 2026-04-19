'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getResult, reprocessOcr, reprocessTranslate, getProviders, updateContentTitle, updateRecordModel, updateRecordLanguage, autoGenerateTitle, continueProcessing, createStreamConnection, API_BASE } from '@/lib/api';
import type { Provider } from '@/lib/providers';
import { flattenModelsForType, getLanguages, type LanguagePrompt } from '@/lib/providers';
import ModelSettingsModal from '@/components/ModelSettingsModal';
import PromptSettingsModal from '@/components/PromptSettingsModal';
import ReprocessModal from '@/components/ReprocessModal';
import ExportModal from '@/components/ExportModal';
import CustomDropdown from '@/components/CustomDropdown';
import ResizablePanels from '@/components/ResizablePanels';
import ImageViewer from '@/components/ImageViewer';

interface PageBlock {
  pageNum: number;
  content: string;
}

function parsePageBlocks(text: string | null): PageBlock[] {
  if (!text) return [];
  const blocks: PageBlock[] = [];
  const regex = /=== Page (\d+) ===\n([\s\S]*?)(?=(=== Page \d+ ===)|$)/g;
  let match;
  while ((match = regex.exec(text)) !== null) {
    blocks.push({
      pageNum: parseInt(match[1]),
      content: match[2].trim()
    });
  }
  return blocks;
}

function getCompletedPages(text: string | null): number {
  if (!text) return 0;
  const blocks = parsePageBlocks(text);
  return blocks.filter(b => b.content && !b.content.startsWith('Error:')).length;
}

export default function ResultPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false); // Start with false to show content immediately
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [isReprocessingOcr, setIsReprocessingOcr] = useState(false);
  const [isReprocessingTrans, setIsReprocessingTrans] = useState(false);
  const [showReprocessModal, setShowReprocessModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [showModelModal, setShowModelModal] = useState(false);
  const [showPromptModal, setShowPromptModal] = useState(false);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [languages, setLanguages] = useState<LanguagePrompt[]>([]);
  const [docLanguage, setDocLanguage] = useState<string>('auto');
  const [savingLanguage, setSavingLanguage] = useState(false);
  const [selectedOcrModel, setSelectedOcrModel] = useState<string>('');
  const [selectedTransModel, setSelectedTransModel] = useState<string>('');
  const [detectedLanguage, setDetectedLanguage] = useState<string>('jp');
  const [editingTitle, setEditingTitle] = useState(false);
  const [titleInput, setTitleInput] = useState('');
  const [pageInput, setPageInput] = useState<string>('');
  const [isEditingPage, setIsEditingPage] = useState(false);
  const [showLanguageSelect, setShowLanguageSelect] = useState(false);
  const [isDetecting, setIsDetecting] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const imageViewerRef = useRef<{ reset: () => void; zoomIn: () => void; zoomOut: () => void } | null>(null);
  const ocrScrollRef = useRef<HTMLDivElement>(null);
  const transScrollRef = useRef<HTMLDivElement>(null);
  const reprocessingOcrPageRef = useRef<number | null>(null);
  const reprocessingTransPageRef = useRef<number | null>(null);
  const prevOcrContentRef = useRef<string>('');
  const prevTransContentRef = useRef<string>('');
  const stuckProgressRef = useRef<{ocr: number; trans: number; count: number}>({ocr: 0, trans: 0, count: 0});
  const hasCalledContinueRef = useRef<boolean>(false);
  const fetchingRef = useRef<boolean>(false);
  const isMountedRef = useRef<boolean>(true);

  const fetchResult = useCallback(async () => {
    if (fetchingRef.current || !isMountedRef.current) return;
    fetchingRef.current = true;
    try {
      const data = await getResult(id);
      if (!isMountedRef.current) return;
      setResult(data);
      setError(null);
      
      if (data.status === 'language_detection_failed') {
        setShowLanguageSelect(true);
        setIsDetecting(false);
      } else if ((data.status === 'pending' || data.status === 'processing') && data.doc_language === 'auto' && !data.model_endpoint) {
        setIsDetecting(true);
        setShowLanguageSelect(false);
      } else if (data.model_endpoint) {
        setIsDetecting(false);
        setShowLanguageSelect(false);
        setDetectedLanguage(data.model_endpoint);
      }
      
      const dataTotalPages = data.total_pages ? parseInt(data.total_pages) : 1;
      const dataOcrComplete = getCompletedPages(data.ocr_text);
      const dataTransComplete = getCompletedPages(data.translated_text);
      const dataIsComplete = dataOcrComplete >= dataTotalPages && dataTransComplete >= dataTotalPages && dataTotalPages > 0;
      
      if (data.total_pages) {
        setTotalPages(parseInt(data.total_pages) || 1);
      } else if (data.ocr_text) {
        const blocks = parsePageBlocks(data.ocr_text);
        setTotalPages(blocks.length || 1);
      }
      
      if (data.status === 'completed' && !data.content_title && data.ocr_text) {
        if (!isMountedRef.current) return;
        try {
          const titleData = await autoGenerateTitle(id);
          if (!isMountedRef.current) return;
          if (titleData.generated) {
            setResult((prev: any) => prev ? ({ ...prev, content_title: titleData.content_title }) : null);
          }
        } catch (err) {
          console.error('Failed to auto-generate title:', err);
        }
      }
    } catch (err: any) {
      if (isMountedRef.current) {
        if (err.code !== 'ECONNABORTED' && err.code !== 'ERR_CANCELED' && err.response?.status !== 504) {
          console.error('Failed to load result:', err);
        }
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
      fetchingRef.current = false;
    }
  }, [id, selectedOcrModel, selectedTransModel, docLanguage, detectedLanguage]);

  useEffect(() => {
    isMountedRef.current = true;
    fetchResult();
    const interval = setInterval(fetchResult, 10000);
    return () => {
      clearInterval(interval);
      isMountedRef.current = false;
    };
  }, [fetchResult]);

  useEffect(() => {
    if (!result || result.status !== 'processing') return;
    
    const eventSource = createStreamConnection(id);
    
    eventSource.onmessage = (event) => {
      if (!isMountedRef.current) return;
      try {
        const data = JSON.parse(event.data);
        
        let newOcrText = result.ocr_text || '';
        let newTranslatedText = result.translated_text || '';
        
        Object.keys(data).forEach(key => {
          if (key.startsWith('ocr_page_')) {
            const pageNum = parseInt(key.replace('ocr_page_', ''), 10);
            const pageContent = data[key];
            const pageRegex = new RegExp(`=== Page ${pageNum} ===\\n[^]*?(?=\\n\\n=== Page \\d+ ===|$)`);
            if (pageRegex.test(newOcrText)) {
              newOcrText = newOcrText.replace(pageRegex, `=== Page ${pageNum} ===\n${pageContent}`);
            } else {
              const pageHeader = `=== Page ${pageNum} ===\n${pageContent}`;
              if (newOcrText) {
                newOcrText = newOcrText + '\n\n' + pageHeader;
              } else {
                newOcrText = pageHeader;
              }
            }
          }
          
          if (key.startsWith('trans_page_')) {
            const pageNum = parseInt(key.replace('trans_page_', ''), 10);
            const pageContent = data[key];
            const pageRegex = new RegExp(`=== Page ${pageNum} ===\\n[^]*?(?=\\n\\n=== Page \\d+ ===|$)`);
            if (pageRegex.test(newTranslatedText)) {
              newTranslatedText = newTranslatedText.replace(pageRegex, `=== Page ${pageNum} ===\n${pageContent}`);
            } else {
              const pageHeader = `=== Page ${pageNum} ===\n${pageContent}`;
              if (newTranslatedText) {
                newTranslatedText = newTranslatedText + '\n\n' + pageHeader;
              } else {
                newTranslatedText = pageHeader;
              }
            }
          }
        });
        
        if (newOcrText !== result.ocr_text || newTranslatedText !== result.translated_text) {
          setResult((prev: any) => ({
            ...prev,
            ocr_text: newOcrText,
            translated_text: newTranslatedText,
          }));
        }
        
        if (data.status === 'completed' || data.status === 'failed') {
          eventSource.close();
          fetchResult();
        }
      } catch (e) {
        console.error('Stream parse error:', e);
      }
    };
    
    eventSource.onerror = () => {
      eventSource.close();
    };
    
    return () => {
      eventSource.close();
    };
  }, [id, result?.status]);

  useEffect(() => {
    getProviders().then(data => {
      setProviders(data);
    }).catch(console.error);
    getLanguages().then(data => {
      setLanguages(data);
    }).catch(console.error);
  }, []);

  const prevResultRef = useRef<any>(null);
  
  useEffect(() => {
    if (result && providers.length > 0 && languages.length > 0) {
      const prevResult = prevResultRef.current;
      const resultChanged = !prevResult || 
        prevResult.ocr_model_id !== result.ocr_model_id ||
        prevResult.translate_model_id !== result.translate_model_id ||
        prevResult.doc_language !== result.doc_language ||
        prevResult.model_endpoint !== result.model_endpoint;
      
      if (resultChanged) {
        prevResultRef.current = result;
        
        const storedOcrModel = result.ocr_model_id || '';
        const storedTransModel = result.translate_model_id || '';
        const storedDocLanguage = result.doc_language || 'auto';
        const detected = result.model_endpoint;
        
        const isValidLanguage = languages.some(l => l.language_code === detected);
        const finalDetected = isValidLanguage ? detected : 'en';
        setDetectedLanguage(finalDetected);
        setDocLanguage(storedDocLanguage);
        
        const models = flattenModelsForType(providers, 'both');
        
        if (storedOcrModel && models.some(m => `${m.providerId}/${m.modelId}` === storedOcrModel)) {
          setSelectedOcrModel(storedOcrModel);
        } else if (models.length > 0) {
          setSelectedOcrModel(`${models[0].providerId}/${models[0].modelId}`);
        }
        
        if (storedTransModel && models.some(m => `${m.providerId}/${m.modelId}` === storedTransModel)) {
          setSelectedTransModel(storedTransModel);
        } else if (models.length > 0) {
          setSelectedTransModel(`${models[0].providerId}/${models[0].modelId}`);
        }
      }
    }
  }, [result, providers, languages]);

  const handlePageChange = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
    }
  };

  const scrollToPage = (page: number) => {
    setTimeout(() => {
      const ocrBlock = ocrScrollRef.current?.querySelector(`[data-page="${page}"]`);
      if (ocrBlock) {
        ocrBlock.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
      const transBlock = transScrollRef.current?.querySelector(`[data-page="${page}"]`);
      if (transBlock) {
        transBlock.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }, 100);
  };

  useEffect(() => {
    scrollToPage(currentPage);
  }, [currentPage]);

  const handleJumpToPage = (page: number) => {
    setCurrentPage(page);
  };

  const handleSaveTitle = async () => {
    if (!titleInput.trim()) {
      setEditingTitle(false);
      return;
    }
    try {
      await updateContentTitle(id, titleInput.trim());
      setResult((prev: any) => ({ ...prev, content_title: titleInput.trim() }));
      setEditingTitle(false);
    } catch (err) {
      console.error('Failed to update title:', err);
    }
  };

  const handleReprocessOcr = async (page: number) => {
    if (isReprocessingOcr) return;
    setIsReprocessingOcr(true);
    reprocessingOcrPageRef.current = page;
    prevOcrContentRef.current = getOcrContentForPage(page);
    
    const eventSource = createStreamConnection(id);
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data[`ocr_page_${page}`]) {
          setResult((prev: any) => {
            const pageContent = data[`ocr_page_${page}`];
            const pageRegex = new RegExp(`=== Page ${page} ===\\n[^]*?(?=\\n\\n=== Page \\d+ ===|$)`);
            let newOcrText = prev.ocr_text || '';
            if (pageRegex.test(newOcrText)) {
              newOcrText = newOcrText.replace(pageRegex, `=== Page ${page} ===\n${pageContent}`);
            }
            return { ...prev, ocr_text: newOcrText };
          });
        }
        
        if (data[`trans_page_${page}`]) {
          setResult((prev: any) => {
            const pageContent = data[`trans_page_${page}`];
            const pageRegex = new RegExp(`=== Page ${page} ===\\n[^]*?(?=\\n\\n=== Page \\d+ ===|$)`);
            let newTransText = prev.translated_text || '';
            if (pageRegex.test(newTransText)) {
              newTransText = newTransText.replace(pageRegex, `=== Page ${page} ===\n${pageContent}`);
            }
            return { ...prev, translated_text: newTransText };
          });
        }
        
        if (data.status === 'completed') {
          eventSource.close();
          setIsReprocessingOcr(false);
          reprocessingOcrPageRef.current = null;
          fetchResult();
        }
      } catch (e) {
        console.error('Stream parse error:', e);
      }
    };
    
    eventSource.onerror = () => {
      eventSource.close();
      setIsReprocessingOcr(false);
      reprocessingOcrPageRef.current = null;
    };
    
    try {
      const actualLanguage = docLanguage === 'auto' ? detectedLanguage : docLanguage;
      await reprocessOcr(id, page, selectedOcrModel, getEndpointFromModel(selectedOcrModel), actualLanguage);
    } catch (err) {
      console.error('Reprocess OCR failed:', err);
      eventSource.close();
      setIsReprocessingOcr(false);
      reprocessingOcrPageRef.current = null;
    }
  };

  const handleReprocessTranslate = async (page: number) => {
    if (isReprocessingTrans) return;
    setIsReprocessingTrans(true);
    reprocessingTransPageRef.current = page;
    prevTransContentRef.current = getTransContentForPage(page);
    
    const eventSource = createStreamConnection(id);
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data[`trans_page_${page}`]) {
          setResult((prev: any) => {
            const pageContent = data[`trans_page_${page}`];
            const pageRegex = new RegExp(`=== Page ${page} ===\\n[^]*?(?=\\n\\n=== Page \\d+ ===|$)`);
            let newTransText = prev.translated_text || '';
            if (pageRegex.test(newTransText)) {
              newTransText = newTransText.replace(pageRegex, `=== Page ${page} ===\n${pageContent}`);
            }
            return { ...prev, translated_text: newTransText };
          });
        }
        
        if (data.status === 'completed') {
          eventSource.close();
          setIsReprocessingTrans(false);
          reprocessingTransPageRef.current = null;
          fetchResult();
        }
      } catch (e) {
        console.error('Stream parse error:', e);
      }
    };
    
    eventSource.onerror = () => {
      eventSource.close();
      setIsReprocessingTrans(false);
      reprocessingTransPageRef.current = null;
    };
    
    try {
      await reprocessTranslate(id, page, selectedTransModel, getEndpointFromModel(selectedTransModel));
    } catch (err) {
      console.error('Reprocess translate failed:', err);
      eventSource.close();
      setIsReprocessingTrans(false);
      reprocessingTransPageRef.current = null;
    }
  };

  const getEndpointFromModel = (modelId: string): string => {
    const providerId = modelId.split('/')[0];
    const provider = providers.find(p => p.id.toString() === providerId);
    return provider?.base_url || '';
  };

  const handleSwitchModel = () => {
    setShowModelModal(true);
  };

  const handleReprocessSuccess = async () => {
    await fetchResult();
  };

  const ocrBlocks = parsePageBlocks(result?.ocr_text);
  const transBlocks = parsePageBlocks(result?.translated_text);

  useEffect(() => {
    if (reprocessingOcrPageRef.current !== null) {
      const page = reprocessingOcrPageRef.current;
      const currentContent = ocrBlocks.find(b => b.pageNum === page)?.content || '';
      if (currentContent && currentContent !== prevOcrContentRef.current && !currentContent.startsWith('Error:')) {
        setIsReprocessingOcr(false);
        reprocessingOcrPageRef.current = null;
      }
    }
  }, [result, ocrBlocks]);

  useEffect(() => {
    if (reprocessingTransPageRef.current !== null) {
      const page = reprocessingTransPageRef.current;
      const currentContent = transBlocks.find(b => b.pageNum === page)?.content || '';
      if (currentContent && currentContent !== prevTransContentRef.current && !currentContent.startsWith('Error:')) {
        setIsReprocessingTrans(false);
        reprocessingTransPageRef.current = null;
      }
    }
  }, [result, transBlocks]);

  const completedOcrPages = getCompletedPages(result?.ocr_text);
  const completedTransPages = getCompletedPages(result?.translated_text);

  const ocrProgress = totalPages > 0 ? Math.round((completedOcrPages / totalPages) * 100) : 0;
  const transProgress = totalPages > 0 ? Math.round((completedTransPages / totalPages) * 100) : 0;

  const isOcrComplete = completedOcrPages >= totalPages && totalPages > 0;
  const isTransComplete = completedTransPages >= totalPages && totalPages > 0;
  const isAllComplete = isOcrComplete && isTransComplete;
  const isProcessing = result?.status === 'processing' || result?.status === 'uploaded' || (!isAllComplete && result?.status === 'completed');
  
  const isOcrProcessing = !isOcrComplete && isProcessing;
  const isTransProcessing = !isTransComplete && isProcessing;

  const getOcrContentForPage = (pageNum: number) => {
    return ocrBlocks.find(b => b.pageNum === pageNum)?.content || '';
  };

  const getTransContentForPage = (pageNum: number) => {
    return transBlocks.find(b => b.pageNum === pageNum)?.content || '';
  };

  const handleGoHome = useCallback(() => {
    window.dispatchEvent(new Event('refresh-home-data'));
    router.push('/');
  }, [router]);

  if (loading && !result) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button onClick={handleGoHome} className="text-blue-600 hover:text-blue-800 underline">
            返回首页
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      {isDetecting && !showLanguageSelect && (
        <div className="bg-blue-50 border-b border-blue-300 px-4 py-2 flex items-center gap-2 shrink-0">
          <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
          <span className="text-blue-800 text-sm">识别语种中...</span>
        </div>
      )}
      {showLanguageSelect && !isDetecting && (
        <div className="bg-red-50 border-b border-red-300 px-4 py-2 shrink-0">
          <span className="text-red-800 text-sm">语种识别失败，请手动选择语种</span>
        </div>
      )}
      <header className="bg-white shadow-sm shrink-0">
        <div className="px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button onClick={handleGoHome} className="flex items-center gap-1">
                <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                <img src="/logo.png" alt="Logo" className="h-5 w-auto" />
              </button>
              <span className="text-gray-300">|</span>
              <h1 className="text-lg font-bold text-gray-900 truncate max-w-xs">{result?.original_filename}</h1>
              {result?.content_title && (
                editingTitle ? (
                  <input
                    type="text"
                    value={titleInput}
                    onChange={(e) => setTitleInput(e.target.value)}
                    onBlur={handleSaveTitle}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleSaveTitle();
                      if (e.key === 'Escape') setEditingTitle(false);
                    }}
                    className="text-sm text-black px-1 py-0.5 border border-gray-300 rounded focus:outline-none"
                    style={{ width: `${Math.max(200, titleInput.length * 14 + 24)}px`, maxWidth: '600px' }}
                    autoFocus
                  />
                ) : (
                  <span
                    onDoubleClick={() => {
                      setTitleInput(result.content_title || '');
                      setEditingTitle(true);
                    }}
                    className="text-sm text-black cursor-pointer"
                    title="双击编辑"
                  >
                    {result.content_title}
                  </span>
                )
              )}
            </div>
            <div className="flex items-center gap-2 relative">
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                isAllComplete ? 'bg-green-100 text-green-800' :
                isProcessing ? 'bg-yellow-100 text-yellow-800' :
                result?.status === 'failed' ? 'bg-red-100 text-red-800' :
                'bg-gray-100 text-gray-800'
              }`}>
              {isAllComplete ? '处理完成' :
               isProcessing ? '处理中...' :
               result?.status === 'failed' ? '处理失败' : '等待中'}
              </span>
              <span className="text-gray-300">|</span>
              <button onClick={handleSwitchModel} suppressHydrationWarning className="px-3 py-1.5 text-xs font-medium text-white rounded hover:opacity-80 transition-opacity" style={{ backgroundColor: '#8FA3A6' }}>模型设置</button>
              <button onClick={() => setShowPromptModal(true)} suppressHydrationWarning className="px-3 py-1.5 text-xs font-medium text-white rounded hover:opacity-80 transition-opacity" style={{ backgroundColor: '#B5A8B5' }}>提示词设置</button>
              <button onClick={() => setShowReprocessModal(true)} suppressHydrationWarning className="px-3 py-1.5 text-xs font-medium text-white rounded hover:opacity-80 transition-opacity" style={{ backgroundColor: '#C4A484' }}>重新处理</button>
              <button onClick={() => setShowExportModal(true)} suppressHydrationWarning className="px-3 py-1.5 text-xs font-medium text-white rounded hover:opacity-80 transition-opacity" style={{ backgroundColor: '#7D9D9C' }}>结果导出</button>
            </div>
          </div>
        </div>
      </header>

      <ResizablePanels>
        <div className="bg-white border-r border-gray-200 flex flex-col h-full">
          <div className="shrink-0 px-3 border-b flex items-center gap-2" style={{ paddingTop: '4px', paddingBottom: '4px', backgroundColor: '#f9fafb' }}>
            <h2 className="text-sm font-semibold text-gray-900">原始文档</h2>
            <div className="flex-1" />
            <CustomDropdown
              size="sm"
              value={docLanguage}
              onChange={async (val) => {
                if (val !== docLanguage) {
                  setSavingLanguage(true);
                  try {
                    await updateRecordLanguage(id, val);
                    setDocLanguage(val);
                    setShowLanguageSelect(false);
                    const actualLanguage = val === 'auto' ? detectedLanguage : val;
                    if (selectedOcrModel && selectedTransModel) {
                      await continueProcessing(id, selectedOcrModel, selectedTransModel, getEndpointFromModel(selectedOcrModel), actualLanguage);
                    }
                  } catch (err) {
                    console.error('Failed to save language:', err);
                  } finally {
                    setSavingLanguage(false);
                  }
                }
              }}
              options={[
                { value: 'auto', label: languages.find(l => l.language_code === detectedLanguage)?.language_name ? `自动检测（${languages.find(l => l.language_code === detectedLanguage)?.language_name}）` : '自动检测' },
                ...languages.map((lang) => ({
                  value: lang.language_code,
                  label: lang.language_name
                }))
              ]}
              disabled={savingLanguage}
            />
            <div className="flex-1" />
            <div className="flex items-center gap-2">
              <div className="flex items-center bg-gray-50 border border-gray-200 rounded overflow-hidden">
                <button onClick={() => imageViewerRef.current?.zoomOut()} className="px-2 py-1 text-gray-900 text-xs hover:bg-gray-100">−</button>
                <div className="w-px h-4 bg-gray-200" />
                <button onClick={() => imageViewerRef.current?.reset()} className="px-2 py-1 text-gray-900 text-xs hover:bg-gray-100">↻</button>
                <div className="w-px h-4 bg-gray-200" />
                <button onClick={() => imageViewerRef.current?.zoomIn()} className="px-2 py-1 text-gray-900 text-xs hover:bg-gray-100">＋</button>
              </div>
              {result?.file_type === 'pdf' ? (
                <>
                  <button onClick={() => handlePageChange(currentPage - 1)} disabled={currentPage <= 1} className="px-2 py-1 text-gray-900 bg-gray-50 border border-gray-200 rounded text-xs hover:bg-gray-100 disabled:opacity-50">←</button>
                  {isEditingPage ? (
                    <input
                      type="text"
                      value={pageInput}
                      onChange={(e) => setPageInput(e.target.value)}
                      onBlur={() => {
                        const num = parseInt(pageInput, 10);
                        if (num >= 1 && num <= totalPages) {
                          handlePageChange(num);
                        }
                        setIsEditingPage(false);
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          const num = parseInt(pageInput, 10);
                          if (num >= 1 && num <= totalPages) {
                            handlePageChange(num);
                          }
                          setIsEditingPage(false);
                        }
                        if (e.key === 'Escape') {
                          setIsEditingPage(false);
                        }
                      }}
                      className="w-10 text-center text-xs text-gray-900 bg-gray-50 border border-gray-200 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                      autoFocus
                    />
                  ) : (
                    <span
                      onClick={() => {
                        setPageInput(String(currentPage));
                        setIsEditingPage(true);
                      }}
                      className="text-xs text-gray-700 cursor-pointer hover:text-gray-900"
                    >
                      {currentPage}
                    </span>
                  )}
                  <span className="text-xs text-gray-700">/ {totalPages}</span>
                  <button onClick={() => handlePageChange(currentPage + 1)} disabled={currentPage >= totalPages} className="px-2 py-1 text-gray-900 bg-gray-50 border border-gray-200 rounded text-xs hover:bg-gray-100 disabled:opacity-50">→</button>
                </>
              ) : null}
            </div>
          </div>
          <div className="flex-1 overflow-hidden" ref={containerRef}>
            {result?.file_type === 'jpg' && (
              <ImageViewer
                ref={imageViewerRef}
                src={`${API_BASE}/result/file/${id}`}
                fileType="jpg"
              />
            )}
            {result?.file_type === 'pdf' && (
              <ImageViewer
                ref={imageViewerRef}
                src={`${API_BASE}/result/page/${id}/${currentPage}`}
                fileType="pdf"
              />
            )}
          </div>
        </div>

        <div className="bg-white border-r border-gray-200 flex flex-col h-full">
          <div className="shrink-0 px-3 border-b flex items-center gap-2" style={{ paddingTop: '4px', paddingBottom: '4px', backgroundColor: '#f9fafb' }}>
            <h2 className="text-sm font-semibold text-gray-900">外文识别</h2>
            <div className="flex-1" />
            <CustomDropdown
              className={isOcrProcessing ? 'w-1/3' : 'w-1/2'}
              size="sm"
              value={selectedOcrModel}
              onChange={async (val) => {
                setSelectedOcrModel(val);
                try {
                  await updateRecordModel(id, val, undefined);
                  const actualLanguage = docLanguage === 'auto' ? detectedLanguage : docLanguage;
                  await continueProcessing(id, val, selectedTransModel, getEndpointFromModel(val), actualLanguage);
                } catch (err) {
                  console.error('Failed to save OCR model:', err);
                }
              }}
              options={flattenModelsForType(providers, 'both').map((m) => ({
                value: `${m.providerId}/${m.modelId}`,
                label: m.displayName
              }))}
            />
            {!isOcrProcessing && <div className="flex-1" />}
            <div className="flex items-center gap-2">
              {isOcrProcessing ? null : (
                <button
                  onClick={() => handleReprocessOcr(currentPage)}
                  disabled={isReprocessingOcr}
                  className="p-1 text-gray-900 hover:bg-gray-100 disabled:opacity-50"
                  title="重新识别当前页"
                >
                  <svg className={`w-4 h-4 ${isReprocessingOcr ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                </button>
              )}
              {completedOcrPages >= totalPages ? (
                <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <div className="flex items-center gap-2 w-32">
                  <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500 transition-all duration-300" style={{ width: `${ocrProgress}%` }}></div>
                  </div>
                  <span className="text-xs text-gray-500 whitespace-nowrap">{completedOcrPages} / {totalPages}</span>
                </div>
              )}
            </div>
          </div>
          <div className="flex-1 overflow-auto" ref={ocrScrollRef}>
            {ocrBlocks.length > 0 && ocrBlocks.some(b => b.content) ? (
              <div className="p-2 flex flex-col gap-2">
                {ocrBlocks.filter(b => b.content).map(block => (
                  <div
                    data-page={block.pageNum}
                    key={block.pageNum}
                    onClick={() => handleJumpToPage(block.pageNum)}
                    onContextMenu={(e) => {
                      e.stopPropagation();
                    }}
                    className={`text-base px-3 py-2 rounded cursor-pointer ${
                      block.pageNum === currentPage ? 'text-gray-900 bg-gray-50 border border-gray-200' : 'text-gray-900 bg-transparent border border-transparent hover:border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    <span className="inline-block px-1.5 py-0.5 mr-1 text-xs font-semibold rounded bg-blue-100 text-blue-800">P{block.pageNum}</span> <span className="whitespace-pre-wrap break-all">{block.content}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-400 text-base">
                {isOcrProcessing ? '正在识别...' : '尚未识别'}
              </div>
            )}
          </div>
        </div>

        <div className="bg-white flex flex-col h-full">
          <div className="shrink-0 px-3 border-b flex items-center gap-2" style={{ paddingTop: '4px', paddingBottom: '4px', backgroundColor: '#f9fafb' }}>
            <h2 className="text-sm font-semibold text-gray-900">中文翻译</h2>
            <div className="flex-1" />
            <CustomDropdown
              className={isTransProcessing ? 'w-1/3' : 'w-1/2'}
              size="sm"
              value={selectedTransModel}
              onChange={async (val) => {
                setSelectedTransModel(val);
                try {
                  await updateRecordModel(id, undefined, val);
                  const actualLanguage = docLanguage === 'auto' ? detectedLanguage : docLanguage;
                  await continueProcessing(id, selectedOcrModel, val, getEndpointFromModel(selectedOcrModel), actualLanguage);
                } catch (err) {
                  console.error('Failed to save translation model:', err);
                }
              }}
              options={flattenModelsForType(providers, 'both').map((m) => ({
                value: `${m.providerId}/${m.modelId}`,
                label: m.displayName
              }))}
            />
            {!isTransProcessing && <div className="flex-1" />}
            <div className="flex items-center gap-2">
              {isTransProcessing ? null : (
                <button
                  onClick={() => handleReprocessTranslate(currentPage)}
                  disabled={isReprocessingTrans}
                  className="p-1 text-gray-900 hover:bg-gray-100 disabled:opacity-50"
                  title="重新翻译当前页"
                >
                  <svg className={`w-4 h-4 ${isReprocessingTrans ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                </button>
              )}
              {completedTransPages >= totalPages ? (
                <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <div className="flex items-center gap-2 w-32">
                  <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div className="h-full bg-green-500 transition-all duration-300" style={{ width: `${transProgress}%` }}></div>
                  </div>
                  <span className="text-xs text-gray-500 whitespace-nowrap">{completedTransPages} / {totalPages}</span>
                </div>
              )}
            </div>
          </div>
          <div className="flex-1 overflow-auto" ref={transScrollRef}>
            {transBlocks.length > 0 && transBlocks.some(b => b.content) ? (
              <div className="p-2 flex flex-col gap-2">
                {transBlocks.filter(b => b.content).map(block => (
                  <div
                    data-page={block.pageNum}
                    key={block.pageNum}
                    onClick={() => handleJumpToPage(block.pageNum)}
                    onContextMenu={(e) => {
                      e.stopPropagation();
                    }}
                    className={`text-base px-3 py-2 rounded cursor-pointer ${
                      block.pageNum === currentPage ? 'text-gray-900 bg-gray-50 border border-gray-200' : 'text-gray-900 bg-transparent border border-transparent hover:border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    <span className="inline-block px-1.5 py-0.5 mr-1 text-xs font-semibold rounded bg-green-100 text-green-800">P{block.pageNum}</span> <span className="whitespace-pre-wrap break-all">{block.content}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-400 text-base">
                {isTransProcessing ? '正在处理...' : '尚未翻译'}
              </div>
            )}
          </div>
        </div>
      </ResizablePanels>

      <ModelSettingsModal
        isOpen={showModelModal}
        onClose={() => setShowModelModal(false)}
        onModelsChange={() => {
          getProviders().then(data => {
            setProviders(data);
          }).catch(console.error);
          fetchResult();
        }}
      />

      <PromptSettingsModal
        isOpen={showPromptModal}
        onClose={() => setShowPromptModal(false)}
        onPromptsChange={() => {
          getLanguages().then(data => {
            setLanguages(data);
          }).catch(console.error);
        }}
      />

      <ReprocessModal
        isOpen={showReprocessModal}
        onClose={() => setShowReprocessModal(false)}
        recordId={id}
        onSuccess={handleReprocessSuccess}
        initialOcrModel={selectedOcrModel}
        initialTransModel={selectedTransModel}
      />

      <ExportModal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        recordId={id}
        filename={result?.original_filename || ''}
      />
    </div>
  );
}