"use client";

import { useEffect, useRef } from "react";
import {
  CandlestickSeries,
  ColorType,
  createChart,
  type IChartApi,
  type ISeriesApi,
  type Time,
} from "lightweight-charts";
import type { Candle } from "@/lib/api";

type Props = {
  candles: Candle[];
  height?: number;
  markers?: { time: string; type: "buy" | "sell"; price: number }[];
};

export function CandleChart({ candles, height = 420 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      height,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#5A6672",
        fontFamily: "var(--font-sans), system-ui, sans-serif",
      },
      grid: {
        vertLines: { color: "rgba(16,20,24,0.06)" },
        horzLines: { color: "rgba(16,20,24,0.06)" },
      },
      rightPriceScale: { borderVisible: false },
      timeScale: { borderVisible: false, timeVisible: false },
      crosshair: {
        vertLine: { color: "rgba(12,143,106,0.35)", labelBackgroundColor: "#0C8F6A" },
        horzLine: { color: "rgba(12,143,106,0.35)", labelBackgroundColor: "#0C8F6A" },
      },
    });

    const series = chart.addSeries(CandlestickSeries, {
      upColor: "#0C8F6A",
      downColor: "#C23B3B",
      borderUpColor: "#0C8F6A",
      borderDownColor: "#C23B3B",
      wickUpColor: "#0C8F6A",
      wickDownColor: "#C23B3B",
    });

    chartRef.current = chart;
    seriesRef.current = series;

    const onResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    onResize();
    window.addEventListener("resize", onResize);

    return () => {
      window.removeEventListener("resize", onResize);
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, [height]);

  useEffect(() => {
    if (!seriesRef.current || !chartRef.current || !candles.length) return;
    seriesRef.current.setData(
      candles.map((c) => ({
        time: c.time as Time,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      }))
    );
    chartRef.current.timeScale().fitContent();
  }, [candles]);

  return (
    <div className="relative w-full overflow-hidden rounded-sm bg-chart">
      <div ref={containerRef} className="w-full" />
    </div>
  );
}
