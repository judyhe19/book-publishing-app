// src/features/books/components/SeriesPicker.jsx
import React, { useState, useRef } from "react";
import { FormField, Input } from "../../../shared/components";

/**
 * Series name + position picker with autocomplete and auto-populated position.
 *
 * Props:
 *   seriesName         string   current series name value
 *   setSeriesName      fn
 *   seriesPosition     string   current series position value (as string)
 *   setSeriesPosition  fn
 *   seriesOptions      [{name, count}]  all existing series loaded by parent
 *   originalSeriesName string | null   the book's series name before any edits
 *                                      (null when creating a new book)
 *
 * Position autopopulation rules:
 *   - Fires when a series is selected from the dropdown OR when the typed text
 *     exactly matches a known series name.
 *   - If the matched series is the same as originalSeriesName, the position
 *     is left unchanged (the book is already placed there).
 *   - Once autofilled for a series in this session, re-selecting/re-typing
 *     that same series never overwrites the position again (preserves manual edits).
 *   - If the selected series differs (or this is a new book), position is set
 *     to count + 1 (append at end of the target series).
 */
export default function SeriesPicker({
  seriesName,
  setSeriesName,
  seriesPosition,
  setSeriesPosition,
  seriesOptions = [],
  originalSeriesName = null,
}) {
  const [dropdownOpen, setDropdownOpen] = useState(false);

  // Tracks which series position was last autofilled for. Initialized to
  // originalSeriesName so that clicking the same series in edit mode never
  // re-autofills a position the user may already have edited.
  const positionAutofilledFor = useRef(originalSeriesName ?? null);

  const typed = (seriesName || "").trim();
  const typedLower = typed.toLowerCase();

  const suggestions = seriesOptions
    .filter((s) => s.name.toLowerCase().includes(typedLower))
    .slice(0, 20);

  const exactMatch = seriesOptions.find(
    (s) => s.name.toLowerCase() === typedLower
  );

  // Called only when user explicitly clicks a suggestion or the "create" option.
  function applySeriesName(name) {
    setSeriesName(name);
    setDropdownOpen(false);

    // Case 1: same series the book was already in before editing started —
    // leave the position alone (it's already correct).
    const isSameAsOriginal =
      originalSeriesName &&
      originalSeriesName.toLowerCase() === name.toLowerCase();

    // Case 2: position was already autofilled for this exact series in this
    // editing session (e.g. user accidentally re-clicks the same suggestion,
    // or double-clicks). Don't overwrite a position they may have edited.
    const alreadyFilledForThis =
      positionAutofilledFor.current !== null &&
      positionAutofilledFor.current.toLowerCase() === name.toLowerCase();

    if (!isSameAsOriginal && !alreadyFilledForThis) {
      const match = seriesOptions.find(
        (s) => s.name.toLowerCase() === name.toLowerCase()
      );
      const count = match ? match.count : 0;
      setSeriesPosition(String(count + 1));
      positionAutofilledFor.current = name;
    }
  }

  // Typing updates the text and opens the dropdown. If the typed value exactly
  // matches a known series, autofill position using the same guards as
  // applySeriesName so position isn't reset after the user manually edits it.
  function onSeriesInputChange(e) {
    const value = e.target.value;
    setSeriesName(value);
    setDropdownOpen(true);

    const valueTrimmedLower = value.trim().toLowerCase();
    if (valueTrimmedLower) {
      const match = seriesOptions.find(
        (s) => s.name.toLowerCase() === valueTrimmedLower
      );
      if (match) {
        const isSameAsOriginal =
          originalSeriesName &&
          originalSeriesName.toLowerCase() === match.name.toLowerCase();
        const alreadyFilledForThis =
          positionAutofilledFor.current !== null &&
          positionAutofilledFor.current.toLowerCase() === match.name.toLowerCase();
        if (!isSameAsOriginal && !alreadyFilledForThis) {
          setSeriesPosition(String(match.count + 1));
          positionAutofilledFor.current = match.name;
        }
      }
    }
  }

  function onClear() {
    setSeriesName("");
    setSeriesPosition("");
    setDropdownOpen(false);
    positionAutofilledFor.current = null;
  }

  // Valid range hint
  const matchForHint = seriesOptions.find(
    (s) => s.name.toLowerCase() === typedLower
  );
  const countForHint = matchForHint ? matchForHint.count : 0;
  const isOriginalForHint =
    originalSeriesName &&
    originalSeriesName.toLowerCase() === typedLower;
  // When editing within the same series the book is already counted,
  // so max is countForHint (remove self, then re-insert anywhere in 1..count).
  // For a different or new series, max is countForHint + 1.
  const maxPos = typed
    ? isOriginalForHint
      ? countForHint
      : countForHint + 1
    : null;

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {/* Series name with autocomplete */}
        <FormField label="Series name (optional)">
          <div className="relative">
            <Input
              value={seriesName}
              onChange={onSeriesInputChange}
              onFocus={() => setDropdownOpen(true)}
              onBlur={() =>
                setTimeout(() => setDropdownOpen(false), 150)
              }
              placeholder="e.g. The Lord of the Rings"
              autoComplete="off"
            />
            {dropdownOpen && (
              <div className="absolute z-20 mt-1 w-full rounded-xl border border-slate-200 bg-white shadow-lg overflow-hidden">
                {typed.length === 0 ? (
                  <div className="px-3 py-2 text-sm text-slate-500">
                    Start typing to search series…
                  </div>
                ) : suggestions.length === 0 ? (
                  <div className="px-3 py-2 text-sm text-slate-500">
                    New series — will be created on save
                  </div>
                ) : (
                  <ul className="max-h-56 overflow-auto">
                    {suggestions.map((s) => (
                      <li key={s.name}>
                        <button
                          type="button"
                          className="w-full text-left px-3 py-2 text-sm hover:bg-slate-50 flex justify-between"
                          onMouseDown={(ev) => ev.preventDefault()}
                          onClick={() => applySeriesName(s.name)}
                        >
                          <span>{s.name}</span>
                          <span className="text-slate-400 text-xs ml-2">
                            {s.count} {s.count === 1 ? "book" : "books"}
                          </span>
                        </button>
                      </li>
                    ))}
                    {!exactMatch && typed && (
                      <li>
                        <button
                          type="button"
                          className="w-full text-left px-3 py-2 text-sm text-slate-400 hover:bg-slate-50 italic"
                          onMouseDown={(ev) => ev.preventDefault()}
                          onClick={() => applySeriesName(typed)}
                        >
                          Create "{typed}" as new series
                        </button>
                      </li>
                    )}
                  </ul>
                )}
              </div>
            )}
          </div>
        </FormField>

        {/* Position */}
        <FormField label="Series position (optional)">
          <Input
            type="number"
            min="1"
            max={maxPos || undefined}
            value={seriesPosition}
            onChange={(e) => setSeriesPosition(e.target.value)}
            placeholder="e.g. 1"
            disabled={!seriesName.trim()}
          />
          {typed && maxPos !== null && (
            <p className="mt-1 text-xs text-slate-400">
              Valid range: 1–{maxPos}. Other books shift to make room.
            </p>
          )}
        </FormField>
      </div>

      {(seriesName || seriesPosition) && (
        <div>
          <button
            type="button"
            className="text-xs text-slate-500 underline hover:text-red-600"
            onClick={onClear}
          >
            Clear series fields
          </button>
        </div>
      )}
    </div>
  );
}
