// src/shared/components/DualScrollContainer.jsx
import React, { useRef, useCallback } from "react";

/**
 * Container with synchronized top and bottom horizontal scrollbars.
 * Used for wide tables that need scrolling with a visible scrollbar at the top.
 * 
 * @param {number} contentWidth - The minimum width of the content (for scrollbar sizing)
 * @param {React.ReactNode} children - The content to display (usually a table)
 */
export function DualScrollContainer({ 
  contentWidth = 1400, 
  children,
  className = "" 
}) {
  const topScrollRef = useRef(null);
  const bottomScrollRef = useRef(null);

  const handleTopScroll = useCallback(() => {
    if (bottomScrollRef.current && topScrollRef.current) {
      bottomScrollRef.current.scrollLeft = topScrollRef.current.scrollLeft;
    }
  }, []);

  const handleBottomScroll = useCallback(() => {
    if (topScrollRef.current && bottomScrollRef.current) {
      topScrollRef.current.scrollLeft = bottomScrollRef.current.scrollLeft;
    }
  }, []);

  return (
    <div className={className}>
      {/* Top scrollbar */}
      <div
        ref={topScrollRef}
        onScroll={handleTopScroll}
        className="overflow-x-auto"
        style={{ height: "20px" }}
      >
        <div style={{ width: `${contentWidth}px`, height: "1px" }} />
      </div>

      {/* Content with bottom scrollbar */}
      <div
        ref={bottomScrollRef}
        onScroll={handleBottomScroll}
        className="overflow-x-auto"
      >
        <div style={{ minWidth: `${contentWidth}px` }}>
          {children}
        </div>
      </div>
    </div>
  );
}

export default DualScrollContainer;
