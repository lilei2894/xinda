'use client';

import { useState, useCallback } from 'react';
import { uploadFile } from '@/lib/api';

interface FileUploadProps {
  onUploadSuccess: (id: string) => void;
  onUploadError: (error: string) => void;
  isUploading: boolean;
}

export default function FileUpload({ onUploadSuccess, onUploadError, isUploading }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);

  const validateFile = (file: File): string | null => {
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/jpg'];
    if (!allowedTypes.includes(file.type)) {
      return 'Only PDF and JPG files are allowed';
    }
    
    const maxSize = 20 * 1024 * 1024;
    if (file.size > maxSize) {
      return 'File size must be less than 20MB';
    }
    
    return null;
  };

  const handleFileUpload = useCallback(async (file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      onUploadError(validationError);
      return;
    }

    setUploadedFileName(file.name);
    setUploadProgress(0);
    let progressInterval: NodeJS.Timeout | undefined;
    try {
      progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            if (progressInterval) clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 200);

      const result = await uploadFile(file);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      setTimeout(() => {
        onUploadSuccess(result.id);
        setUploadProgress(0);
      }, 500);
    } catch (error: any) {
      if (progressInterval) clearInterval(progressInterval);
      setUploadProgress(0);
      setUploadedFileName(null);
      const errorMessage = error.response?.data?.detail || error.message || 'Upload failed';
      onUploadError(errorMessage);
    }
  }, [onUploadSuccess, onUploadError]);

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  }, [handleFileUpload]);

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  }, [handleFileUpload]);

  const displayText = () => {
    if (isUploading) return '上传中...';
    if (uploadedFileName) return uploadedFileName;
    return '拖拽文件到此处或点击上传';
  };

  return (
    <div className="w-full h-full">
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`
          relative border-2 border-dashed rounded-lg p-12 text-center transition-colors h-full flex flex-col justify-center bg-white
          ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}
          ${isUploading ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
        `}
      >
        <input
          type="file"
          accept=".pdf,.jpg,.jpeg"
          onChange={handleFileSelect}
          className="hidden"
          id="file-upload"
          disabled={isUploading}
          suppressHydrationWarning
        />
        
        <label htmlFor="file-upload" className="cursor-pointer">
          <div className="mb-4">
            <svg
              className={`mx-auto h-16 w-16 ${isDragging ? 'text-blue-500' : 'text-gray-400'}`}
              stroke="currentColor"
              fill="none"
              viewBox="0 0 48 48"
            >
              <path
                d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          
          <div className="text-lg font-medium text-gray-700 mb-2">
            {displayText()}
          </div>
          
          <div className="text-sm text-gray-500">
            支持 PDF 或 JPG 文件，最大 20MB
          </div>
        </label>
      </div>

      {isUploading && uploadProgress > 0 && (
        <div className="mt-4">
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-600 transition-all duration-200"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
          <div className="text-center text-sm text-gray-600 mt-2">
            {uploadProgress}%
          </div>
        </div>
      )}
    </div>
  );
}
