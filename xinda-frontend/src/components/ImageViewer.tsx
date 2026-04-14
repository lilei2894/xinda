'use client';

import { useEffect, useRef, forwardRef, useImperativeHandle } from 'react';
import Panzoom, { PanzoomObject } from '@panzoom/panzoom';

interface ImageViewerProps {
  src: string;
  fileType: 'jpg' | 'pdf';
}

const ImageViewer = forwardRef<{ reset: () => void; zoomIn: () => void; zoomOut: () => void }, ImageViewerProps>(
  ({ src }, ref) => {
    const wrapperRef = useRef<HTMLDivElement | null>(null);
    const panzoomRef = useRef<PanzoomObject | null>(null);

    useEffect(() => {
      const wrapper = wrapperRef.current;
      if (!wrapper) return;

      let wheelHandler: ((e: WheelEvent) => void) | null = null;

      const panzoom = Panzoom(wrapper, {
        minScale: 0.25,
        maxScale: 5,
        startScale: 1,
      });

      panzoomRef.current = panzoom;

      wheelHandler = (e: WheelEvent) => {
        e.preventDefault();
        panzoom.zoomWithWheel(e);
      };

      const container = wrapper.parentElement;
      if (container) {
        container.addEventListener('wheel', wheelHandler, { passive: false });
      }

      return () => {
        if (wheelHandler && container) {
          container.removeEventListener('wheel', wheelHandler);
        }
        panzoomRef.current?.destroy?.();
        panzoomRef.current = null;
      };
    }, []);

    useImperativeHandle(ref, () => ({
      reset: () => {
        panzoomRef.current?.reset?.({ animate: false });
      },
      zoomIn: () => {
        panzoomRef.current?.zoomIn?.();
      },
      zoomOut: () => {
        panzoomRef.current?.zoomOut?.();
      },
    }));

    return (
      <div className="w-full h-full overflow-hidden bg-gray-100 flex items-center justify-center" style={{ cursor: 'grab' }}>
        <div ref={wrapperRef}>
          <img
            src={src}
            alt="Document"
            draggable={false}
            style={{
              maxWidth: '100%',
              maxHeight: '100%',
              objectFit: 'contain',
              display: 'block',
            }}
          />
        </div>
      </div>
    );
  }
);

ImageViewer.displayName = 'ImageViewer';

export default ImageViewer;