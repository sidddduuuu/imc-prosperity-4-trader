"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { EquityPoint } from "@/lib/api";
import { formatMoney } from "@/lib/api";

type Props = {
  data: EquityPoint[];
};

export function EquityChart({ data }: Props) {
  return (
    <div className="h-[340px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="eq" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#0C8F6A" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#0C8F6A" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="bh" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#3D5A80" stopOpacity={0.25} />
              <stop offset="100%" stopColor="#3D5A80" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="rgba(16,20,24,0.06)" vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fill: "#5A6672", fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            minTickGap={48}
          />
          <YAxis
            tick={{ fill: "#5A6672", fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
            width={52}
          />
          <Tooltip
            contentStyle={{
              background: "#F2F4F1",
              border: "1px solid rgba(16,20,24,0.12)",
              borderRadius: 4,
              fontSize: 12,
            }}
            formatter={(value) => formatMoney(Number(value ?? 0))}
          />
          <Legend />
          <Area
            type="monotone"
            dataKey="equity"
            name="Strategy"
            stroke="#0C8F6A"
            fill="url(#eq)"
            strokeWidth={2}
            dot={false}
          />
          <Area
            type="monotone"
            dataKey="buy_hold"
            name="Buy & Hold"
            stroke="#3D5A80"
            fill="url(#bh)"
            strokeWidth={1.5}
            strokeDasharray="4 4"
            dot={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
