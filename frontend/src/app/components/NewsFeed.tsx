import { Newspaper } from "lucide-react";
import type { PortData } from "../data/ports";

interface NewsFeedProps {
  news: PortData["news"];
}

const CATEGORY_COLORS = {
  operations: "text-blue-400 bg-blue-500/10",
  infrastructure: "text-purple-400 bg-purple-500/10",
  trade: "text-emerald-400 bg-emerald-500/10",
  incident: "text-red-400 bg-red-500/10",
};

export function NewsFeed({ news }: NewsFeedProps) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-6">
      <div className="flex items-center gap-2 mb-6">
        <Newspaper className="w-4 h-4 text-zinc-400" />
        <p className="text-sm text-zinc-400">Recent News</p>
      </div>

      <div className="space-y-4">
        {news.map((item, index) => (
          <div
            key={index}
            className="pb-4 border-b border-zinc-800 last:border-b-0 last:pb-0 hover:bg-zinc-800/30 -mx-3 px-3 py-2 rounded transition-colors cursor-pointer"
          >
            <div className="flex items-start gap-3 mb-2">
              <span className={`text-xs px-2 py-0.5 rounded ${CATEGORY_COLORS[item.category]} capitalize`}>
                {item.category}
              </span>
              <span className="text-xs text-zinc-500">{item.time}</span>
            </div>
            <p className="text-sm leading-relaxed mb-1">{item.title}</p>
            <p className="text-xs text-zinc-500">{item.source}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
