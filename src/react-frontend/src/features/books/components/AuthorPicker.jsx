// src/features/books/components/AuthorPicker.jsx
import React, { useState } from "react";
import { FormField, Input } from "../../../shared/components";

/**
 * Single-author picker with search dropdown.
 * Used in BookDetailPage for selecting one author.
 */
export default function AuthorPicker({
  authorOptions,
  selectedAuthorId,
  setSelectedAuthorId,
  authorSearch,
  setAuthorSearch,
}) {
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const filteredAuthors = authorOptions.filter((a) =>
    (a.name || "").toLowerCase().includes(authorSearch.toLowerCase())
  );

  function selectAuthor(a) {
    setSelectedAuthorId(String(a.id));
    setAuthorSearch(a.name);
    setDropdownOpen(false);
  }

  return (
    <FormField label="Author">
      <div className="relative">
        <Input
          value={authorSearch}
          onChange={(e) => {
            setAuthorSearch(e.target.value);
            setDropdownOpen(true);
            if (!e.target.value) setSelectedAuthorId("");
          }}
          onFocus={() => setDropdownOpen(true)}
          onBlur={() => {
            // Delay to allow click on dropdown item
            setTimeout(() => setDropdownOpen(false), 150);
          }}
          placeholder="Search authors…"
        />
        {dropdownOpen && filteredAuthors.length > 0 && (
          <ul className="absolute z-20 mt-1 max-h-48 w-full overflow-auto rounded-md border border-slate-200 bg-white shadow-lg">
            {filteredAuthors.map((a) => (
              <li key={a.id}>
                <button
                  type="button"
                  className="w-full px-3 py-2 text-left text-sm hover:bg-slate-100"
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
