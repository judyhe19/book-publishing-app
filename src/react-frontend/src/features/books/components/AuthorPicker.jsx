// src/features/books/components/AuthorPicker.jsx
import React, { useState } from "react";
import { FormField, Input } from "../../../shared/components";

/**
 * Single-author picker with search dropdown.
 * Used in BookDetailPage for selecting one author.
 *
 * Keyboard navigation:
 *   Tab / Shift+Tab — move highlight down / up within the open dropdown
 *   Enter           — select the highlighted item
 *   Escape          — close the dropdown
 */
export default function AuthorPicker({
  authorOptions,
  selectedAuthorId,
  setSelectedAuthorId,
  authorSearch,
  setAuthorSearch,
}) {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);

  const filteredAuthors = authorOptions.filter((a) =>
    (a.name || "").toLowerCase().includes(authorSearch.toLowerCase())
  );

  function selectAuthor(a) {
    setSelectedAuthorId(String(a.id));
    setAuthorSearch(a.name);
    setDropdownOpen(false);
    setHighlightedIndex(-1);
  }

  function onKeyDown(e) {
    const count = filteredAuthors.length;
    const isOpen = dropdownOpen && count > 0;

    if (e.key === "Tab" && !e.shiftKey && isOpen) {
      e.preventDefault();
      setHighlightedIndex((i) => (i + 1) % count);
    } else if (e.key === "Tab" && e.shiftKey && isOpen) {
      e.preventDefault();
      setHighlightedIndex((i) => (i <= 0 ? count - 1 : i - 1));
    } else if (e.key === "Enter" && isOpen && highlightedIndex >= 0) {
      e.preventDefault();
      selectAuthor(filteredAuthors[highlightedIndex]);
    } else if (e.key === "Escape") {
      setDropdownOpen(false);
      setHighlightedIndex(-1);
    }
  }

  return (
    <FormField label="Author">
      <div className="relative">
        <Input
          value={authorSearch}
          onChange={(e) => {
            const value = e.target.value;
            setAuthorSearch(value);
            setDropdownOpen(true);
            setHighlightedIndex(-1);
            const match = authorOptions.find(
              (a) => (a.name || "").toLowerCase() === value.toLowerCase()
            );
            setSelectedAuthorId(match ? String(match.id) : "");
          }}
          onFocus={() => setDropdownOpen(true)}
          onBlur={() => {
            setTimeout(() => {
              setDropdownOpen(false);
              setHighlightedIndex(-1);
            }, 150);
          }}
          onKeyDown={onKeyDown}
          placeholder="Search authors…"
        />
        {dropdownOpen && filteredAuthors.length > 0 && (
          <ul className="absolute z-20 mt-1 max-h-48 w-full overflow-auto rounded-md border border-slate-200 bg-white shadow-lg">
            {filteredAuthors.map((a, i) => (
              <li key={a.id}>
                <button
                  type="button"
                  className={`w-full px-3 py-2 text-left text-sm ${
                    i === highlightedIndex ? "bg-slate-100" : "hover:bg-slate-100"
                  }`}
                  onMouseDown={() => selectAuthor(a)}
                >
                  {a.name}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </FormField>
  );
}
