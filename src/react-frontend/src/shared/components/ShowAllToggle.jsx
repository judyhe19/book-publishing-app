// src/shared/components/ShowAllToggle.jsx
import React from "react";
import { Button } from "./Button";

/**
 * Toggle between paginated and "show all" views.
 * Common pattern across list pages.
 */
export function ShowAllToggle({ showAll, onToggle, className = "" }) {
  return (
    <Button 
      variant="secondary" 
      onClick={onToggle}
      className={className}
    >
      {showAll ? "Paginate" : "Show all"}
    </Button>
  );
}

export default ShowAllToggle;
