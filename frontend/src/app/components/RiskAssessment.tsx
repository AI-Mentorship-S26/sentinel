import { Shield, AlertTriangle } from "lucide-react";
import type { PortData } from "../data/ports";

interface RiskAssessmentProps {
  risks: PortData["risks"];
}

const RISK_CONFIG = {
  low: {
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/30",
  },
  moderate: {
    color: "text-yellow-400",
    bg: "bg-yellow-500/10",
    border: "border-yellow-500/30",
  },
  high: {
    color: "text-orange-400",
    bg: "bg-orange-500/10",
    border: "border-orange-500/30",
  },
  critical: {
    color: "text-red-400",
    bg: "bg-red-500/10",
    border: "border-red-500/30",
  },
};

export function RiskAssessment({ risks }: RiskAssessmentProps) {
  const overallConfig = RISK_CONFIG[risks.overall];

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-6">
      <div className="flex items-center gap-2 mb-6">
        <Shield className="w-4 h-4 text-zinc-400" />
        <p className="text-sm text-zinc-400">Risk Assessment</p>
      </div>

      {/* Overall Risk */}
      <div className={`rounded-lg border ${overallConfig.border} ${overallConfig.bg} p-4 mb-6`}>
        <p className="text-xs text-zinc-400 mb-1">Overall Risk Level</p>
        <p className={`text-xl capitalize ${overallConfig.color}`}>{risks.overall}</p>
      </div>

      {/* Risk Categories */}
      <div className="space-y-4">
        {risks.categories.map((category, index) => {
          const config = RISK_CONFIG[category.level];
          return (
            <div key={index} className="pb-4 border-b border-zinc-800 last:border-b-0 last:pb-0">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  {category.level === "high" || category.level === "critical" ? (
                    <AlertTriangle className={`w-4 h-4 ${config.color}`} />
                  ) : (
                    <div className={`w-2 h-2 rounded-full ${config.bg} ${config.border} border`} />
                  )}
                  <p className="text-sm">{category.name}</p>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded ${config.bg} ${config.color} capitalize`}>
                  {category.level}
                </span>
              </div>
              <p className="text-xs text-zinc-500 leading-relaxed">{category.description}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
