"use client";

import { useEffect, useMemo, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { X } from "lucide-react";
import OptionWheel from "@/components/OptionWheel";

export type WheelOption = {
  label: string;
  href: string;
};

type Props = {
  open: boolean;
  onClose: () => void;
  options: WheelOption[];
};

export function OptionsMenu({ open, onClose, options }: Props) {
  const router = useRouter();
  const pathname = usePathname();
  const items = useMemo(() => options.map((o) => o.label), [options]);

  const defaultSelected = useMemo(() => {
    const idx = options.findIndex(
      (o) => pathname === o.href || pathname.startsWith(`${o.href}/`)
    );
    return idx >= 0 ? idx : 0;
  }, [options, pathname]);

  const [selected, setSelected] = useState(defaultSelected);

  useEffect(() => {
    if (open) setSelected(defaultSelected);
  }, [open, defaultSelected]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "Enter") {
        const opt = options[selected];
        if (opt) {
          router.push(opt.href);
          onClose();
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose, options, selected, router]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[80]">
      <button
        type="button"
        aria-label="Close options"
        className="absolute inset-0 bg-ink/40 backdrop-blur-[2px]"
        onClick={onClose}
      />

      <aside className="absolute inset-y-0 left-0 flex w-full max-w-md flex-col border-r border-ink/10 bg-ink text-paper shadow-lift">
        <div className="flex items-center justify-between px-6 py-5">
          <div>
            <p className="text-[11px] uppercase tracking-[0.22em] text-paper/50">Options</p>
            <h2 className="mt-1 font-display text-2xl tracking-tight">Navigate Atlas</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-sm border border-paper/15 p-2 text-paper/70 transition hover:border-paper/30 hover:text-paper"
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        <div className="relative min-h-0 flex-1 px-2 pb-8">
          <OptionWheel
            items={items}
            defaultSelected={defaultSelected}
            textColor="#6b7280"
            activeColor="#12B886"
            side="left"
            fontSize={2.1}
            spacing={1.55}
            curve={1}
            tilt={7}
            blur={1.6}
            fade={0.28}
            smoothing={180}
            inset={48}
            loop={false}
            draggable
            soundUrl=""
            soundVolume={0.4}
            onChange={(index: number) => setSelected(index)}
            className="option-wheel--atlas h-full"
          />
        </div>

        <div className="border-t border-paper/10 px-6 py-4">
          <button
            type="button"
            className="w-full bg-signal py-3 text-sm font-medium text-paper transition hover:bg-signal-bright"
            onClick={() => {
              const opt = options[selected];
              if (!opt) return;
              router.push(opt.href);
              onClose();
            }}
          >
            Open {options[selected]?.label || "selection"}
          </button>
          <p className="mt-2 text-center text-[11px] text-paper/45">
            Scroll, drag, or use arrow keys · Enter to open · Esc to close
          </p>
        </div>
      </aside>
    </div>
  );
}
