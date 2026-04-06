'use client';

import { useState, useRef, useEffect } from 'react';

interface Option {
  value: string;
  label: string;
}

interface CustomDropdownProps {
  value: string;
  onChange: (value: string) => void;
  options: Option[];
  className?: string;
  placeholder?: string;
  disabled?: boolean;
  size?: 'sm' | 'default';
  width?: string;
}

function DropdownOption({
  option,
  isSelected,
  padding,
  textClass,
  onClick
}: {
  option: Option;
  isSelected: boolean;
  padding: string;
  textClass: string;
  onClick: () => void;
}) {
  const textRef = useRef<HTMLSpanElement>(null);
  const containerRef = useRef<HTMLButtonElement>(null);
  const [shouldScroll, setShouldScroll] = useState(false);
  const [scrollDistance, setScrollDistance] = useState(0);
  const [isHovered, setIsHovered] = useState(false);

  useEffect(() => {
    if (textRef.current && containerRef.current) {
      const textWidth = textRef.current.scrollWidth;
      const containerWidth = containerRef.current.clientWidth;
      if (textWidth > containerWidth) {
        setShouldScroll(true);
        setScrollDistance(textWidth - containerWidth + 16);
      } else {
        setShouldScroll(false);
        setScrollDistance(0);
      }
    }
  }, [option.label]);

  const animationDuration = Math.max(1.5, scrollDistance / 50);

  return (
    <button
      ref={containerRef}
      type="button"
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={`w-full ${padding} ${textClass} text-left hover:bg-gray-100 overflow-hidden ${
        isSelected ? 'bg-blue-50 text-blue-600' : 'text-gray-900'
      }`}
    >
      <span
        ref={textRef}
        className="inline-block whitespace-nowrap"
        style={shouldScroll && isHovered ? {
          '--scroll-distance': `${scrollDistance}px`,
          animation: `scroll-marquee ${animationDuration}s ease-in-out infinite alternate`
        } as React.CSSProperties : undefined}
      >
        {option.label}
      </span>
    </button>
  );
}

export default function CustomDropdown({
  value,
  onChange,
  options,
  className = '',
  placeholder = '请选择',
  disabled = false,
  size = 'default',
  width
}: CustomDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const selectedOption = options.find(opt => opt.value === value);

  const isSmall = size === 'sm';
  const btnPadding = isSmall ? 'px-2 py-1' : 'px-3 py-2';
  const btnText = isSmall ? 'text-xs' : 'text-sm';
  const iconSize = isSmall ? 'w-3 h-3' : 'w-4 h-4';
  const optionPadding = isSmall ? 'px-2 py-1.5' : 'px-3 py-2';
  const optionText = isSmall ? 'text-xs' : 'text-sm';

  return (
    <div ref={dropdownRef} className={`relative ${className}`} style={width ? { width } : undefined}>
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={`w-full ${btnPadding} ${btnText} bg-white border border-gray-300 rounded-md text-gray-900 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 flex items-center gap-1 justify-between disabled:opacity-50 disabled:cursor-not-allowed`}
      >
        <span className="truncate block">{selectedOption?.label || placeholder}</span>
        <svg
          className={`${iconSize} flex-shrink-0 transition-transform text-gray-500 ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute z-50 top-full left-0 mt-1 bg-white border border-gray-200 rounded-md shadow-lg w-full max-h-60 overflow-y-auto">
          {options.map((option) => (
            <DropdownOption
              key={option.value}
              option={option}
              isSelected={option.value === value}
              padding={optionPadding}
              textClass={optionText}
              onClick={() => {
                onChange(option.value);
                setIsOpen(false);
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
