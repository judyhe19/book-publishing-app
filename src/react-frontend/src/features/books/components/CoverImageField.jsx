// src/features/books/components/CoverImageField.jsx
import React, { useRef, useState, useEffect } from "react";
import { FormField, Button, ErrorAlert } from "../../../shared/components";
import CoverImage from "./CoverImage";

const ALLOWED_TYPES = ["image/jpeg", "image/gif", "image/png", "image/webp"];
const ALLOWED_EXTENSIONS = ".jpg,.jpeg,.gif,.png,.webp";

/**
 * Cover image file picker with preview.
 * Accepts JPEG, GIF, PNG, and WEBP formats.
 * 
 * Does NOT upload immediately - instead passes the File object to parent
 * via onFileChange so upload can happen on form submit.
 * 
 * @param {Object} props
 * @param {string} props.value - Current image path (from database)
 * @param {Function} props.onChange - Called with path (for clearing existing image)
 * @param {Function} props.onFileChange - Called with File object when user selects a new file (null when cleared)
 * @param {string} props.title - Book title for alt text
 * @param {string} props.label - Field label
 */
export default function CoverImageField({
  value,
  onChange,
  onFileChange,
  title = "",
  label = "Cover image (optional)",
  imageClassName,
}) {
  const fileInputRef = useRef(null);
  const [error, setError] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);

  // Clean up object URL when component unmounts or preview changes
  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!ALLOWED_TYPES.includes(file.type)) {
      setError("Invalid format. Please select a JPEG, GIF, PNG, or WEBP image.");
      return;
    }

    // Validate file size (max 5MB)
    const maxSize = 5 * 1024 * 1024;
    if (file.size > maxSize) {
      setError("File too large. Maximum size is 5MB.");
      return;
    }

    setError(null);

    // Clean up old preview URL
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    // Create local preview
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);

    // Pass file to parent (upload happens on save)
    onFileChange?.(file);
  };

  const handleClear = () => {
    setError(null);
    
    // Clean up preview URL
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    
    // Clear file input
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }

    // Notify parent
    onChange("");
    onFileChange?.(null);
  };

  // Use preview URL if available (new file selected), otherwise use saved value
  const displayUrl = previewUrl || value;
  const hasImage = displayUrl && displayUrl.trim().length > 0;

  return (
    <FormField label={label}>
      <input
        ref={fileInputRef}
        type="file"
        accept={ALLOWED_EXTENSIONS}
        onChange={handleFileSelect}
        className="hidden"
      />

      <div className="flex items-center gap-3">
        <Button type="button" variant="secondary" onClick={handleClick}>
          {hasImage ? "Change Image" : "Choose Image"}
        </Button>

        {hasImage && (
          <button
            type="button"
            className="text-sm text-red-500 underline hover:text-red-700"
            onClick={handleClear}
          >
            Remove
          </button>
        )}

        {!hasImage && (
          <span className="text-sm text-slate-400">
            JPEG, GIF, PNG, or WEBP (max 5MB)
          </span>
        )}
      </div>

      {error && (
        <ErrorAlert variant="warning" className="mt-2">
          {error}
        </ErrorAlert>
      )}

      {hasImage && (
        <div className="mt-3">
          <CoverImage path={displayUrl} title={title} className={imageClassName} />
        </div>
      )}
    </FormField>
  );
}
