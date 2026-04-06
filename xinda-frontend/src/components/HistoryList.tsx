'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { getHistory, deleteHistory } from '@/lib/api';

export default function HistoryList() {
  const pathname = usePathname();
  const [records, setRecords] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [refreshKey, setRefreshKey] = useState(0);
  const pageSize = 20;
  const mountedRef = useRef(true);

  useEffect(() => {
    const handler = () => setRefreshKey(k => k + 1);
    window.addEventListener('refresh-home-data', handler);
    return () => window.removeEventListener('refresh-home-data', handler);
  }, []);

  const fetchHistory = async (pageNum: number) => {
    if (!mountedRef.current) return;
    setLoading(true);
    try {
      const data = await getHistory(pageNum, pageSize);
      if (!mountedRef.current) return;
      setRecords(data.records || []);
      setTotal(data.total || 0);
      setTotalPages(Math.ceil((data.total || 0) / pageSize));
      setPage(pageNum);
    } catch (err) {
      if (mountedRef.current) {
        setError(err instanceof Error ? err.message : 'Failed to load history');
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    mountedRef.current = true;
    fetchHistory(1);
    return () => { mountedRef.current = false; };
  }, [refreshKey, pathname]);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('确定要删除这条记录吗？')) return;

    try {
      await deleteHistory(id);
      if (records.length === 1 && page > 1) {
        fetchHistory(page - 1);
      } else {
        fetchHistory(page);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete record');
    }
  };

  const statusLabels: { [key: string]: { text: string; color: string } } = {
    'pending': { text: '等待', color: 'bg-gray-100 text-gray-800' },
    'uploaded': { text: '已上传', color: 'bg-blue-100 text-blue-800' },
    'processing': { text: '处理中', color: 'bg-yellow-100 text-yellow-800' },
    'ocr_done': { text: 'OCR完成', color: 'bg-indigo-100 text-indigo-800' },
    'completed': { text: '已完成', color: 'bg-green-100 text-green-800' },
    'failed': { text: '失败', color: 'bg-red-100 text-red-800' }
  };

  const handleRowClick = (id: string, status: string) => {
    if (status !== 'pending') {
      window.location.href = `/result/${id}`;
    }
  };

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-800">{error}</p>
        <button
          onClick={() => fetchHistory(page)}
          className="mt-2 text-sm text-red-600 hover:text-red-800"
        >
          重试
        </button>
      </div>
    );
  }

  return (
    <div className="mt-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">历史记录</h2>
      
      {loading && records.length === 0 ? (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">加载中...</p>
        </div>
      ) : records.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          暂无历史记录
        </div>
      ) : (
        <>
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-48">
                      文件名
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider" style={{ width: '20em' }}>
                      文件内容
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-12">
                      页数
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-36">
                      上传时间
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-24">
                      状态
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-24">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {records.map((record) => {
                    const status = statusLabels[record.status] || { text: record.status, color: 'bg-gray-100 text-gray-800' };
                    const isClickable = record.status !== 'pending';
                    return (
                      <tr
                        key={record.id}
                        onClick={() => handleRowClick(record.id, record.status)}
                        className={`${isClickable ? 'cursor-pointer hover:bg-gray-50' : ''}`}
                      >
                        <td className="px-4 py-3 text-sm text-gray-900 text-left">
                          <span className="block max-w-[180px] truncate" title={record.original_filename}>
                            {record.original_filename}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500 text-left" style={{ maxWidth: '20em' }}>
                          <span className="block truncate" title={record.content_title || ''}>
                            {record.content_title || '-'}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500 text-right">
                          {record.total_pages || '-'}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500 text-center">
                          {new Date(record.upload_time).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${status.color}`}>
                            {status.text}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm font-medium text-center">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              window.location.href = `/result/${record.id}`;
                            }}
                            className="text-blue-600 hover:text-blue-900 mr-3"
                          >
                            查看
                          </button>
                          <button
                            onClick={(e) => handleDelete(record.id, e)}
                            className="text-red-600 hover:text-red-900"
                          >
                            删除
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {totalPages > 1 && (
            <div className="mt-4 flex items-center justify-between">
              <div className="text-sm text-gray-600">
                共 {total} 条记录，第 {page} / {totalPages} 页
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => fetchHistory(page - 1)}
                  disabled={page <= 1}
                  className={`px-3 py-1 rounded ${page <= 1 ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-blue-600 text-white hover:bg-blue-700'}`}
                >
                  上一页
                </button>
                <button
                  onClick={() => fetchHistory(page + 1)}
                  disabled={page >= totalPages}
                  className={`px-3 py-1 rounded ${page >= totalPages ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-blue-600 text-white hover:bg-blue-700'}`}
                >
                  下一页
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}