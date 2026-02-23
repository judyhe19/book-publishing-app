// src/features/books/components/AuthorsEditor.jsx
import React, { useMemo } from "react";
import { Button } from "../../../shared/components/Button";

function normalizeName(s) {
  return (s || "").trim().replace(/\s+/g, " ");
}

export function AuthorsEditor({
  authors,
  setAuthors,
  authorOptions,
  authorsLoading,
  openAuthorIdx,
  setOpenAuthorIdx,
}) {
  const selectedNames = useMemo(() => {
    return new Set(
      authors
        .map((a) => normalizeName(a.author_name).toLowerCase())
        .filter(Boolean)
    );
  }, [authors]);

  function updateAuthorRow(idx, patch) {
    setAuthors((prev) =>
      prev.map((row, i) => (i === idx ? { ...row, ...patch } : row))
    );
  }

  function addAuthorRow() {
    setAuthors((prev) => [...prev, { author_name: "", royalty_rate: "0.50" }]);
  }

  function removeAuthorRow(idx) {
    setAuthors((prev) => prev.filter((_, i) => i !== idx));
    setOpenAuthorIdx((cur) => (cur === idx ? null : cur));
  }

  return (
    <div>
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-medium text-slate-700">Authors</div>
          <div className="text-xs text-slate-500">
            Type to filter. Missing names will be created when you save.
          </div>
        </div>

        <Button type="button" variant="secondary" onClick={addAuthorRow}>
          Add author
        </Button>
      </div>

      <div className="mt-3 space-y-2">
        {authors.map((row, idx) => {
          const typed = normalizeName(row.author_name);
          const typedKey = typed.toLowerCase();

          const suggestions = authorOptions
            .filter((a) => {
              const key = normalizeName(a.name).toLowerCase();
              const selectedElsewhere = selectedNames.has(key) && key !== typedKey;
              return !selectedElsewhere && key.includes(typedKey);
            })
            .slice(0, 20);

          const showDropdown = openAuthorIdx === idx && !authorsLoading;

          return (
            <div key={idx} className="flex flex-col gap-2 sm:flex-row sm:items-center">
              <div className="sm:w-[28rem] w-full relative">
                <input
                  className="w-full rounded-xl border border-slate-200 px-3 py-2"
                  value={row.author_name}
                  onChange={(e) => {
                    updateAuthorRow(idx, { author_name: e.target.value });
                    setOpenAuthorIdx(idx);
                  }}
                  onFocus={() => setOpenAuthorIdx(idx)}
                  onBlur={() => {
                    setTimeout(
                      () => setOpenAuthorIdx((cur) => (cur === idx ? null : cur)),
                      120
                    );
                  }}
                  placeholder="Start typing an author..."
                  required
                />

                {showDropdown ? (
                  <div className="absolute z-20 mt-1 w-full rounded-xl border border-slate-200 bg-white shadow-lg overflow-hidden">
                    {typed.length === 0 ? (
                      <div className="px-3 py-2 text-sm text-slate-500">
                        Start typing to search authors…
                      </div>
                    ) : suggestions.length === 0 ? (
                      <div className="px-3 py-2 text-sm text-slate-500">
                        No matches — will create “{typed}” on save
                      </div>
                    ) : (
                      <ul className="max-h-56 overflow-auto">
                        {suggestions.map((a) => (
                          <li key={a.id}>
                            <button
                              type="button"
                              className="w-full text-left px-3 py-2 text-sm hover:bg-slate-50"
                              onMouseDown={(ev) => ev.preventDefault()}
                              onClick={() => {
                                updateAuthorRow(idx, { author_name: a.name });
                                setOpenAuthorIdx(null);
                              }}
                            >
                              {a.name}
                            </button>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                ) : null}
              </div>

              <div className="sm:w-40 w-full">
                <input
                  className="w-full rounded-xl border border-slate-200 px-3 py-2"
                  value={row.royalty_rate}
                  onChange={(e) =>
                    updateAuthorRow(idx, { royalty_rate: e.target.value })
                  }
                  placeholder="0.50"
                  required
                />
              </div>

              {authors.length > 1 ? (
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => removeAuthorRow(idx)}
                >
                  Remove
                </Button>
              ) : null}
            </div>
          );
        })}
      </div>
    </div>
  );
}
