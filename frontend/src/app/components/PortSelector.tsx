import { ChevronDown } from "lucide-react";
import { PORT_DATA } from "../data/ports";

interface PortSelectorProps {
  selectedPortId: string;
  onSelectPort: (portId: string) => void;
}

export function PortSelector({ selectedPortId, onSelectPort }: PortSelectorProps) {
  return (
    <div className="relative">
      <select
        value={selectedPortId}
        onChange={(e) => onSelectPort(e.target.value)}
        className="appearance-none bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-2.5 pr-10 text-sm cursor-pointer hover:border-zinc-600 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent min-w-[280px]"
      >
        {Object.values(PORT_DATA).map((port) => (
          <option key={port.id} value={port.id}>
            {port.name}
          </option>
        ))}
      </select>
      <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400 pointer-events-none" />
    </div>
  );
}
