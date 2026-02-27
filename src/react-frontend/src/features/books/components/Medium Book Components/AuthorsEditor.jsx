// src/features/books/components/AuthorsEditor.jsx
import React, { useMemo } from "react";
import { Button, Input } from "../../../shared/components";

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
  // Evolution 2: exactly ONE author row is supported.
  // Keep the external API (authors/setAuthors) to minimize churn in parent components.
  const row = useMemo(() => {
    const first = authors?.[0] || {};
    return {
      author_id: first.author_id ?? null,
      author_name: first.author_name ?? "",
      distributor_author_royalty_rate:
        first.distributor_author_royalty_rate ?? "0.50",
      hand_sold_author_royalty_rate:
        first.hand_sold_author_royalty_rate ?? "0.20",
    };
  }, [authors]);

  const selectedKey = useMemo(() => normalizeName(row.author_name).toLowerCase(), [row.author_name]);

  function setSingleRow(patch) {
    setAuthors(() => [
      {
        ...row,
        ...patch,
      },
    ]);
  }

  const typed = normalizeName(row.author_name);
  const typedKey = typed.toLowerCase();

  const suggestions = useMemo(() => {
    if (!typedKey) return [];
    return authorOptions
      .filter((a) => normalizeName(a.name).toLowerCase().includes(typedKey))
      .slice(0, 20);
  }, [authorOptions, typedKey]);

  const showDropdown = openAuthorIdx === 0 && !authorsLoading;

  return (
    <div>
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-medium text-slate-700">Author</div>
          <div className="text-xs text-slate-500">
            Select an existing author. New author creation is done elsewhere.
          </div>
        </div>
      </div>

      <div className="mt-3">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          {/* Author name input with dropdown */}
          <div className="sm:w-[28rem] w-full relative">
            <Input
              value={row.author_name}
              onChange={(e) => {
                const v = e.target.value;
                // clear author_id if user edits text
                setSingleRow({ author_name: v, author_id: null });
                setOpenAuthorIdx(0);
              }}
              onFocus={() => setOpenAuthorIdx(0)}
              onBlur={() => {
                setTimeout(
                  () => setOpenAuthorIdx((cur) => (cur === 0 ? null : cur)),
                  120
                );
              }}
              placeholder="Start typing an author..."
              required
            />

            {showDropdown && (
              <div className="absolute z-20 mt-1 w-full rounded-xl border border-slate-200 bg-white shadow-lg overflow-hidden">
                {typed.length === 0 ? (
                  <div className="px-3 py-2 text-sm text-slate-500">
                    Start typing to search authors…
                  </div>
                ) : suggestions.length === 0 ? (
                  <div className="px-3 py-2 text-sm text-slate-500">
                    No matches — author must already exist.
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
                            setSingleRow({ author_name: a.name, author_id: a.id });
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
            )}
          </div>

          {/* Distributor author royalty rate */}
          <div className="sm:w-44 w-full">
            <Input
              value={row.distributor_author_royalty_rate}
              onChange={(e) =>
                setSingleRow({ distributor_author_royalty_rate: e.target.value })
              }
              placeholder="0.50"
              required
            />
            <div className="mt-1 text-[11px] text-slate-500">
              Distributor royalty rate
            </div>
          </div>

          {/* Hand-sold author royalty rate */}
          <div className="sm:w-44 w-full">
            <Input
              value={row.hand_sold_author_royalty_rate}
              onChange={(e) =>
                setSingleRow({ hand_sold_author_royalty_rate: e.target.value })
              }
              placeholder="0.20"
              required
            />
            <div className="mt-1 text-[11px] text-slate-500">
              Hand-sold royalty rate
            </div>
          </div>
        </div>

        {/* Tiny helper if user typed but didn't select */}
        {typed.length > 0 && row.author_id == null && (
          <div className="mt-2 text-xs text-amber-600">
            Please select an existing author from the dropdown.
          </div>
        )}
      </div>
    </div>
  );
}

export default AuthorsEditor;