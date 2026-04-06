'use client';

import { useState } from 'react';

interface DonationModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const AMOUNTS = [
  { value: 5, label: '¥5' },
  { value: 10, label: '¥10' },
  { value: 20, label: '¥20' },
];

export default function DonationModal({ isOpen, onClose }: DonationModalProps) {
  const [selectedAmount, setSelectedAmount] = useState(5);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />

      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-sm overflow-hidden">
        <div className="flex items-center justify-between px-4 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">捐赠支持</h2>
          <button
            onClick={onClose}
            className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="px-6 py-6">
          <p className="text-sm text-gray-600 text-center mb-4">
            感谢您的支持！选择捐赠金额：
          </p>

          <div className="flex gap-3 mb-6">
            {AMOUNTS.map((amount) => (
              <button
                key={amount.value}
                onClick={() => setSelectedAmount(amount.value)}
                className={`flex-1 py-3 text-sm font-medium rounded-lg transition-colors ${
                  selectedAmount === amount.value
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {amount.label}
              </button>
            ))}
          </div>

          <div className="flex items-center justify-center">
            <img
              src={`/donate-${selectedAmount}.png`}
              alt={`捐赠 ${selectedAmount} 元`}
              className="w-100 h-100 object-contain rounded-lg"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
