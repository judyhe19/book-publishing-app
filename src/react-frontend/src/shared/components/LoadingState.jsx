// src/shared/components/LoadingState.jsx
import React from "react";
import { Spinner } from "./Spinner";

/**
 * Consistent loading state display.
 * Can be used inline or as a full-page loader.
 */
export function LoadingState({ 
  message = "Loading...", 
  fullPage = false,
  className = "" 
}) {
  const content = (
    <div className={`flex items-center gap-2 text-slate-500 ${className}`}>
      <Spinner />
      <span>{message}</span>
    </div>
  );

  if (fullPage) {
    return (
      <div className="p-6">
        {content}
      </div>
    );
  }

  return content;
}

export default LoadingState;
