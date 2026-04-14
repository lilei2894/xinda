'use client';

import { useState, useRef, useCallback, ReactNode } from 'react';

interface ResizablePanelsProps {
  children: ReactNode;
  defaultSizes?: number[];
  minSizes?: number[];
}

export default function ResizablePanels({ 
  children, 
  defaultSizes = [34, 33, 33],
  minSizes = [20, 20, 20]
}: ResizablePanelsProps) {
  const [sizes, setSizes] = useState(defaultSizes);
  const containerRef = useRef<HTMLDivElement>(null);
  const isDragging = useRef<number | null>(null);
  const startXRef = useRef(0);
  const startSizesRef = useRef<number[]>(defaultSizes);

  const handleMouseDown = useCallback((index: number, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    isDragging.current = index;
    startXRef.current = e.clientX;
    startSizesRef.current = [...sizes];

    const handleMouseMove = (moveEvent: MouseEvent) => {
      if (!containerRef.current || isDragging.current === null) return;

      const containerRect = containerRef.current.getBoundingClientRect();
      const containerWidth = containerRect.width;
      const deltaX = moveEvent.clientX - startXRef.current;
      const deltaPercent = (deltaX / containerWidth) * 100;

      const startSizes = startSizesRef.current;
      const newSizes = [...startSizes];
      const dragIndex = isDragging.current;

      if (dragIndex === 0) {
        const firstPanelNewSize = startSizes[0] + deltaPercent;
        const minFirst = minSizes[0];
        const minSecond = minSizes[1];
        const maxFirst = 100 - minSecond - minSizes[2];
        newSizes[0] = Math.max(minFirst, Math.min(maxFirst, firstPanelNewSize));
        const diff = newSizes[0] - startSizes[0];
        newSizes[1] = startSizes[1] - diff;
        newSizes[2] = startSizes[2];
      } else if (dragIndex === 1) {
        const secondPanelNewSize = startSizes[1] + deltaPercent;
        const minFirst = minSizes[0];
        const minSecond = minSizes[1];
        const minThird = minSizes[2];
        const maxSecond = 100 - minFirst - minThird;
        newSizes[1] = Math.max(minSecond, Math.min(maxSecond, secondPanelNewSize));
        newSizes[2] = 100 - minFirst - newSizes[1];
      }

      setSizes(newSizes);
    };

    const handleMouseUp = () => {
      isDragging.current = null;
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  }, [sizes, minSizes]);

  const childArray = Array.isArray(children) ? children : [children];

  return (
    <div ref={containerRef} className="flex-1 flex overflow-hidden h-full" style={{ width: '100%' }}>
      {childArray.map((child, index) => (
        <div
          key={index}
          className="flex flex-col overflow-hidden h-full relative"
          style={{ width: `${sizes[index]}%` }}
        >
          {child}
          {index < childArray.length - 1 && (
            <div
              className="absolute right-0 top-0 bottom-0 w-0.5 hover:bg-gray-400 cursor-col-resize bg-gray-300 z-10"
              onMouseDown={(e) => handleMouseDown(index, e)}
              style={{ cursor: 'col-resize' }}
            />
          )}
        </div>
      ))}
    </div>
  );
}
