import { Ship, Clock } from "lucide-react";
import type { PortData } from "../data/ports";

interface CongestionIndicatorProps {
  level: PortData["congestion"];
}

const CONGESTION_CONFIG = {
  low: {
    label: "Low Congestion",
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
    barColor: "bg-emerald-500",
  },
  moderate: {
    label: "Moderate Congestion",
    color: "text-yellow-400",
    bg: "bg-yellow-500/10",
    border: "border-yellow-500/20",
    barColor: "bg-yellow-500",
  },
  high: {
    label: "High Congestion",
    color: "text-orange-400",
    bg: "bg-orange-500/10",
    border: "border-orange-500/20",
    barColor: "bg-orange-500",
  },
  critical: {
    label: "Critical Congestion",
    color: "text-red-400",
    bg: "bg-red-500/10",
    border: "border-red-500/20",
    barColor: "bg-red-500",
  },
};

export function CongestionIndicator({ level }: CongestionIndicatorProps) {
  const config = CONGESTION_CONFIG[level.level];

  return (
    <div className={`rounded-lg border ${config.border} ${config.bg} p-6`}>
      <div className="mb-6">
        <p className="text-sm text-zinc-400 mb-2">Congestion Status</p>
        <p className={`text-2xl ${config.color} tracking-tight`}>{config.label}</p>
      </div>

      {/* Percentage Bar */}
      <div className="mb-6">
        <div className="flex items-end justify-between mb-2">
          <span className="text-sm text-zinc-400">Capacity</span>
          <span className={`text-3xl tabular-nums ${config.color}`}>{level.percentage}%</span>
        </div>
        <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
          <div
            className={`h-full ${config.barColor} transition-all duration-500`}
            style={{ width: `${level.percentage}%` }}
          />
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="space-y-4 pt-4 border-t border-zinc-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-zinc-400">
            <Ship className="w-4 h-4" />
            <span className="text-sm">Vessels Waiting</span>
          </div>
          <span className="text-xl tabular-nums">{level.vesselCount}</span>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-zinc-400">
            <Clock className="w-4 h-4" />
            <span className="text-sm">Avg Wait Time</span>
          </div>
          <span className="text-xl tabular-nums">{level.avgWaitTime}</span>
        </div>
      </div>
    </div>
  );
}
