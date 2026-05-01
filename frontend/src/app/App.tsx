import { useEffect, useState } from "react";
import { PortSelector } from "./components/PortSelector";
import { SatelliteView } from "./components/SatelliteView";
import { CongestionIndicator } from "./components/CongestionIndicator";
import { PortStatistics } from "./components/PortStatistics";
import { NewsFeed } from "./components/NewsFeed";
import { RiskAssessment } from "./components/RiskAssessment";
import { PORT_DATA } from "./data/ports";
import { fetchCongestionScore, scoreToLevel } from "./utils/congestionApi";

export default function App() {
  const [selectedPortId, setSelectedPortId] = useState("houston");
  const selectedPort = PORT_DATA[selectedPortId];

  const [congestion, setCongestion] = useState(selectedPort.congestion);

  useEffect(() => {
    async function updateCongestion() {
      const score = await fetchCongestionScore(selectedPort.name);

      setCongestion({
        ...selectedPort.congestion,
        level: scoreToLevel(score),
        percentage: Math.round(score * 100),
      });
    }
  

    updateCongestion();
  }, [selectedPort]); 
  
  useEffect(() => {
  Object.values(PORT_DATA).forEach((port) => {
    const img = new Image();
    img.src = `http://127.0.0.1:8000/image/${encodeURIComponent(port.name)}`;
  }); 
}, []);

  return (
    <div className="size-full bg-zinc-950 text-zinc-50 overflow-y-auto">
      <div className="min-h-full">
        {/* Header */}
        <header className="border-b border-zinc-800 bg-zinc-950/95 backdrop-blur sticky top-0 z-50">
          <div className="max-w-[1800px] mx-auto px-6 py-4 flex items-center justify-between">
            <div>
              <h1 className="text-xl tracking-tight">US Port Operations</h1>
              <p className="text-zinc-500 text-sm mt-0.5">Real-time monitoring & intelligence</p>
            </div>
            <PortSelector
              selectedPortId={selectedPortId}
              onSelectPort={setSelectedPortId}
            />
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-[1800px] mx-auto px-6 py-8">
          {/* Port Name & Location */}
          <div className="mb-8">
            <h2 className="text-4xl tracking-tight mb-2">{selectedPort.name}</h2>
            <p className="text-zinc-400">{selectedPort.location}</p>
          </div>

          {/* Primary Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            {/* Satellite View - Spans 2 columns */}
            <div className="lg:col-span-2">
              <SatelliteView port={selectedPort} />
            </div>

            {/* Congestion & Quick Stats */}
            <div className="space-y-6">
              <CongestionIndicator level={congestion} />
              <PortStatistics stats={selectedPort.statistics} />
            </div>
          </div>

          {/* Secondary Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <NewsFeed news={selectedPort.news} />
            <RiskAssessment risks={selectedPort.risks} />
          </div>
        </main>
      </div>
    </div>
  );
}