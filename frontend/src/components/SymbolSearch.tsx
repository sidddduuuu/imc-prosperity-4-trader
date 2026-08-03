"use client";

import { useEffect, useRef, useState } from "react";
import { Search } from "lucide-react";
import { atlasApi } from "@/lib/api";

type Result = { symbol: string; name: string; exchange?: string };

type Props = {
  value: string;
  onChange: (symbol: string) => void;
  placeholder?: string;
};

export function SymbolSearch({ value, onChange, placeholder = "Search ticker…" }: Props) {
  const [query, setQuery] = useState(value);
  const [results, setResults] = useState<Result[]>([]);
  const [open, setOpen] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setQuery(value);
  }, [value]);

  useEffect(() => {
    if (query.trim().length < 1) {
      setResults([]);
      return;
    }
    const t = setTimeout(async () => {
      try {
        const data = await atlasApi.search(query.trim());
        setResults(data);
        setOpen(true);
      } catch {
        setResults([]);
      }
    }, 220);
    return () => clearTimeout(t);
  }, [query]);

  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  return (
    <div ref={boxRef} className="relative w-full">
      <div className="flex items-center gap-2 border border-ink/15 bg-paper px-3 py-2.5">
        <Search size={16} className="text-ink-muted" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value.toUpperCase())}
          onFocus={() => results.length && setOpen(true)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && query.trim()) {
              onChange(query.trim().toUpperCase());
              setOpen(false);
            }
          }}
          placeholder={placeholder}
          className="w-full bg-transparent text-sm outline-none placeholder:text-mist"
        />
      </div>
      {open && results.length > 0 && (
        <ul className="absolute z-20 mt-1 max-h-64 w-full overflow-auto border border-ink/10 bg-paper shadow-lift">
          {results.map((r) => (
            <li key={r.symbol}>
              <button
                type="button"
                className="flex w-full items-center justify-between px-3 py-2.5 text-left text-sm hover:bg-paper-warm"
                onClick={() => {
                  onChange(r.symbol);
                  setQuery(r.symbol);
                  setOpen(false);
                }}
              >
                <span className="font-medium text-ink">{r.symbol}</span>
                <span className="truncate pl-4 text-ink-muted">{r.name}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
