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

type RiskLevel = keyof typeof RISK_CONFIG;

function normalizeLevel(level: string): RiskLevel {
  const normalized = level.toLowerCase();

  if (
    normalized === "low" ||
    normalized === "moderate" ||
    normalized === "high" ||
    normalized === "critical"
  ) {
    return normalized;
  }

  return "low";
}

export function RiskAssessment({ risks }: RiskAssessmentProps) {
  const overallLevel = normalizeLevel(risks.overall);
  const overallConfig = RISK_CONFIG[overallLevel];

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-6">
      <div className="mb-6 flex items-center gap-2">
        <Shield className="h-4 w-4 text-zinc-400" />
        <p className="text-sm text-zinc-400">Risk Assessment</p>
      </div>

      {/* Overall Risk */}
      <div
        className={`mb-6 rounded-lg border p-4 ${overallConfig.border} ${overallConfig.bg}`}
      >
        <p className="mb-1 text-xs text-zinc-400">Overall Risk Level</p>
        <p className={`text-xl capitalize ${overallConfig.color}`}>
          {overallLevel}
        </p>
      </div>

      {/* Risk Categories */}
      <div className="space-y-4">
        {risks.categories.map((category, index) => {
          const level = normalizeLevel(category.level);
          const config = RISK_CONFIG[level];

          return (
            <div
              key={index}
              className="border-b border-zinc-800 pb-4 last:border-b-0 last:pb-0"
            >
              <div className="mb-2 flex items-start justify-between">
                <div className="flex items-center gap-2">
                  {level === "high" || level === "critical" ? (
                    <AlertTriangle className={`h-4 w-4 ${config.color}`} />
                  ) : (
                    <div
                      className={`h-2 w-2 rounded-full border ${config.bg} ${config.border}`}
                    />
                  )}

                  <p className="text-sm text-zinc-200">{category.name}</p>
                </div>

                <span
                  className={`rounded px-2 py-0.5 text-xs capitalize ${config.bg} ${config.color}`}
                >
                  {level}
                </span>
              </div>

              <p className="text-xs leading-relaxed text-zinc-500">
                {category.description}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}