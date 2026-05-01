import { MapPin, Loader2 } from "lucide-react";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import type { PortData } from "../data/ports";
import { useState, useEffect } from "react";

interface SatelliteViewProps {
  port: PortData;
}


export function SatelliteView({ port }: SatelliteViewProps) {

  const [imageUrl, setImageUrl] = useState<string | null>(null);
const [loading, setLoading] = useState(false);

useEffect(() => {
  setLoading(true);
  const url = `http://127.0.0.1:8000/image/${encodeURIComponent(port.name.replace(/\//g, "-"))}`;
  const img = new Image();
  img.onload = () => {
    setImageUrl(url);
    setLoading(false);
  };
  img.onerror = () => {
    setLoading(false);
  };
  img.src = url;
}, [port.name]);

  return (
    <div className="relative rounded-lg overflow-hidden bg-zinc-900 border border-zinc-800">
      {loading ? (
  <div className="w-full aspect-[16/10] flex items-center justify-center bg-zinc-900">
    <Loader2 className="w-6 h-6 animate-spin text-zinc-500" />
  </div>
) : (
  <ImageWithFallback
    src={imageUrl ?? port.satelliteImage}
    alt={`Satellite view of ${port.name}`}
    className="w-full aspect-[16/10] object-cover scale-100 origin-center"
  />
)}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-zinc-950/95 via-zinc-950/60 to-transparent p-6 pt-20">
        <div className="flex items-start gap-2 text-zinc-300">
          <MapPin className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm">Coordinates</p>
            <p className="text-xs text-zinc-500 mt-0.5">{port.coordinates}</p>
          </div>
        </div>
      </div>
      <div className="absolute top-4 right-4 bg-zinc-950/80 backdrop-blur-sm px-3 py-1.5 rounded text-xs border border-zinc-700">
        Satellite Imagery
      </div>
    </div>
  );
}
