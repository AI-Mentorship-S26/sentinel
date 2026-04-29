import { TrendingUp, TrendingDown } from "lucide-react";
import type { PortData } from "../data/ports";

interface PortStatisticsProps {
  stats: PortData["statistics"];
}

export function PortStatistics({ stats }: PortStatisticsProps) {
  const isPositiveGrowth = stats.yoyGrowth.startsWith("+");

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-6">
      <p className="text-sm text-zinc-400 mb-6">Key Metrics</p>

      <div className="space-y-5">
        {/* Annual TEU */}
        <div>
          <p className="text-xs text-zinc-500 mb-1">Annual TEU Capacity</p>
          <p className="text-2xl tabular-nums">{stats.annualTEU}</p>
        </div>

        {/* Today's Throughput */}
        <div>
          <p className="text-xs text-zinc-500 mb-1">Throughput Today</p>
          <p className="text-2xl tabular-nums">{stats.throughputToday}</p>
        </div>

        {/* YoY Growth */}
        <div>
          <p className="text-xs text-zinc-500 mb-1">Year-over-Year Growth</p>
          <div className="flex items-center gap-2">
            <p className={`text-2xl tabular-nums ${isPositiveGrowth ? "text-emerald-400" : "text-red-400"}`}>
              {stats.yoyGrowth}
            </p>
            {isPositiveGrowth ? (
              <TrendingUp className="w-5 h-5 text-emerald-400" />
            ) : (
              <TrendingDown className="w-5 h-5 text-red-400" />
            )}
          </div>
        </div>

        {/* Operational Stats */}
        <div className="pt-5 border-t border-zinc-800 grid grid-cols-3 gap-4">
          <div>
            <p className="text-xs text-zinc-500 mb-1">Vessels</p>
            <p className="text-lg tabular-nums">{stats.currentVessels}</p>
          </div>
          <div>
            <p className="text-xs text-zinc-500 mb-1">Berths</p>
            <p className="text-lg tabular-nums">{stats.berths}</p>
          </div>
          <div>
            <p className="text-xs text-zinc-500 mb-1">Cranes</p>
            <p className="text-lg tabular-nums">{stats.craneOperations}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
