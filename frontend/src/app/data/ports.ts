export interface PortData {
  id: string;
  name: string;
  location: string;
  congestion: {
    level: "low" | "moderate" | "high" | "critical";
    percentage: number;
    vesselCount: number;
    avgWaitTime: string;
  };
  statistics: {
    annualTEU: string;
    currentVessels: number;
    berths: number;
    craneOperations: number;
    throughputToday: string;
    yoyGrowth: string;
  };
  news: Array<{
    title: string;
    source: string;
    time: string;
    category: "operations" | "infrastructure" | "trade" | "incident";
  }>;
  risks: {
    overall: "low" | "moderate" | "high" | "critical";
    categories: Array<{
      name: string;
      level: "low" | "moderate" | "high" | "critical";
      description: string;
    }>;
  };
  satelliteImage: string;
  coordinates: string;
}

export const PORT_DATA: Record<string, PortData> = {
  "houston": {
    id: "houston",
    name: "Port of Houston",
    location: "Houston, Texas",
    coordinates: "29.67° N - 29.70° N, 95.02° W - 94.97° W",
    satelliteImage: "https://images.unsplash.com/photo-1569440261201-a19c6c2ab8c4?w=1200&h=800&fit=crop",
    congestion: {
      level: "moderate",
      percentage: 65,
      vesselCount: 42,
      avgWaitTime: "4.8 days",
    },
    statistics: {
      annualTEU: "3.2M",
      currentVessels: 42,
      berths: 41,
      craneOperations: 87,
      throughputToday: "5,671 TEU",
      yoyGrowth: "+2.3%",
    },
    news: [
      {
        title: "Port operations running smoothly",
        source: "Port of Houston Authority",
        time: "2h ago",
        category: "operations",
      },
      {
        title: "Infrastructure upgrades scheduled",
        source: "Maritime Executive",
        time: "5h ago",
        category: "infrastructure",
      },
    ],
    risks: {
      overall: "moderate",
      categories: [
        {
          name: "Security",
          level: "moderate",
          description: "Petrochemical cargo requires enhanced protocols.",
        },
        {
          name: "Weather",
          level: "moderate",
          description: "Monitoring tropical systems.",
        },
        {
          name: "Congestion",
          level: "moderate",
          description: "Normal operational delays.",
        },
      ],
    },
  },
  "long-beach": {
    id: "long-beach",
    name: "Port of Long Beach",
    location: "Long Beach, California",
    coordinates: "33.74° N - 33.77° N, 118.22° W - 118.17° W",
    satelliteImage: "https://images.unsplash.com/photo-1605731414142-a7f9c1b72099?w=1200&h=800&fit=crop",
    congestion: {
      level: "moderate",
      percentage: 58,
      vesselCount: 35,
      avgWaitTime: "3.9 days",
    },
    statistics: {
      annualTEU: "8.1M",
      currentVessels: 35,
      berths: 35,
      craneOperations: 142,
      throughputToday: "10,932 TEU",
      yoyGrowth: "+1.8%",
    },
    news: [
      {
        title: "Container volumes steady",
        source: "Port Authority",
        time: "1h ago",
        category: "operations",
      },
      {
        title: "Environmental compliance targets met",
        source: "Maritime Executive",
        time: "1d ago",
        category: "operations",
      },
    ],
    risks: {
      overall: "low",
      categories: [
        {
          name: "Security",
          level: "low",
          description: "Enhanced screening procedures in place.",
        },
        {
          name: "Weather",
          level: "low",
          description: "Stable weather patterns forecast.",
        },
        {
          name: "Labor",
          level: "low",
          description: "Stable workforce relations.",
        },
      ],
    },
  },
  "los-angeles": {
    id: "los-angeles",
    name: "Port of Los Angeles",
    location: "San Pedro Bay, California",
    coordinates: "33.73° N - 33.76° N, 118.28° W - 118.23° W",
    satelliteImage: "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=1200&h=800&fit=crop",
    congestion: {
      level: "moderate",
      percentage: 62,
      vesselCount: 38,
      avgWaitTime: "4.2 days",
    },
    statistics: {
      annualTEU: "9.3M",
      currentVessels: 38,
      berths: 43,
      craneOperations: 156,
      throughputToday: "12,847 TEU",
      yoyGrowth: "+3.2%",
    },
    news: [
      {
        title: "Container throughput up in Q1 2026",
        source: "Port Authority",
        time: "2h ago",
        category: "operations",
      },
      {
        title: "Automated terminal expansion approved",
        source: "Maritime Executive",
        time: "5h ago",
        category: "infrastructure",
      },
    ],
    risks: {
      overall: "low",
      categories: [
        {
          name: "Security",
          level: "low",
          description: "Standard security protocols in effect.",
        },
        {
          name: "Weather",
          level: "low",
          description: "Clear conditions expected.",
        },
        {
          name: "Labor",
          level: "low",
          description: "Stable workforce.",
        },
      ],
    },
  },
  "seattle": {
    id: "seattle",
    name: "Port of Seattle",
    location: "Seattle, Washington",
    coordinates: "47.59° N - 47.62° N, 122.37° W - 122.32° W",
    satelliteImage: "https://images.unsplash.com/photo-1609775475397-905a92c1f77b?w=1200&h=800&fit=crop",
    congestion: {
      level: "low",
      percentage: 41,
      vesselCount: 22,
      avgWaitTime: "2.1 days",
    },
    statistics: {
      annualTEU: "3.8M",
      currentVessels: 22,
      berths: 29,
      craneOperations: 76,
      throughputToday: "6,234 TEU",
      yoyGrowth: "+5.4%",
    },
    news: [
      {
        title: "Trans-Pacific trade volumes surge",
        source: "Northwest Seaport Alliance",
        time: "4h ago",
        category: "trade",
      },
      {
        title: "Cruise season begins with record bookings",
        source: "Port of Seattle",
        time: "7h ago",
        category: "operations",
      },
    ],
    risks: {
      overall: "low",
      categories: [
        {
          name: "Security",
          level: "low",
          description: "Standard security posture maintained.",
        },
        {
          name: "Weather",
          level: "moderate",
          description: "Fog conditions may impact visibility.",
        },
        {
          name: "Labor",
          level: "low",
          description: "Collaborative labor environment.",
        },
      ],
    },
  },
  "oakland": {
    id: "oakland",
    name: "Port of Oakland",
    location: "Oakland, California",
    coordinates: "37.79° N - 37.82° N, 122.32° W - 122.27° W",
    satelliteImage: "https://images.unsplash.com/photo-1605731413657-9ca9dd4e2135?w=1200&h=800&fit=crop",
    congestion: {
      level: "low",
      percentage: 45,
      vesselCount: 24,
      avgWaitTime: "2.5 days",
    },
    statistics: {
      annualTEU: "2.5M",
      currentVessels: 24,
      berths: 20,
      craneOperations: 58,
      throughputToday: "4,823 TEU",
      yoyGrowth: "+4.1%",
    },
    news: [
      {
        title: "West Coast trade volumes increase",
        source: "Port of Oakland",
        time: "3h ago",
        category: "trade",
      },
      {
        title: "New terminal facilities planned",
        source: "JOC.com",
        time: "1d ago",
        category: "infrastructure",
      },
    ],
    risks: {
      overall: "low",
      categories: [
        {
          name: "Security",
          level: "low",
          description: "Standard protocols active.",
        },
        {
          name: "Weather",
          level: "low",
          description: "Normal conditions.",
        },
        {
          name: "Labor",
          level: "low",
          description: "Stable labor environment.",
        },
      ],
    },
  },
  "ny-nj": {
    id: "ny-nj",
    name: "Port of New York / New Jersey",
    location: "New York Harbor",
    coordinates: "40.64° N - 40.67° N, 74.15° W - 74.10° W",
    satelliteImage: "https://images.unsplash.com/photo-1514565131-fce0801e5785?w=1200&h=800&fit=crop",
    congestion: {
      level: "moderate",
      percentage: 58,
      vesselCount: 32,
      avgWaitTime: "3.1 days",
    },
    statistics: {
      annualTEU: "7.8M",
      currentVessels: 32,
      berths: 38,
      craneOperations: 134,
      throughputToday: "11,204 TEU",
      yoyGrowth: "+4.7%",
    },
    news: [
      {
        title: "Record container volumes in Q1 2026",
        source: "Port Authority NY/NJ",
        time: "3h ago",
        category: "operations",
      },
      {
        title: "Infrastructure improvements ongoing",
        source: "FreightWaves",
        time: "6h ago",
        category: "infrastructure",
      },
    ],
    risks: {
      overall: "moderate",
      categories: [
        {
          name: "Security",
          level: "moderate",
          description: "Heightened security due to metropolitan location.",
        },
        {
          name: "Weather",
          level: "moderate",
          description: "Spring weather variability.",
        },
        {
          name: "Labor",
          level: "low",
          description: "Stable labor relations.",
        },
      ],
    },
  },
  "norfolk": {
    id: "norfolk",
    name: "Port of Virginia (Norfolk)",
    location: "Norfolk, Virginia",
    coordinates: "36.93° N - 36.96° N, 76.37° W - 76.32° W",
    satelliteImage: "https://images.unsplash.com/photo-1605731413577-4593caa00ee7?w=1200&h=800&fit=crop",
    congestion: {
      level: "low",
      percentage: 38,
      vesselCount: 19,
      avgWaitTime: "1.8 days",
    },
    statistics: {
      annualTEU: "3.3M",
      currentVessels: 19,
      berths: 24,
      craneOperations: 72,
      throughputToday: "6,145 TEU",
      yoyGrowth: "+6.2%",
    },
    news: [
      {
        title: "East Coast gateway sees growth",
        source: "Virginia Port Authority",
        time: "2h ago",
        category: "operations",
      },
      {
        title: "Deepwater access attracts larger vessels",
        source: "Maritime Executive",
        time: "1d ago",
        category: "infrastructure",
      },
    ],
    risks: {
      overall: "low",
      categories: [
        {
          name: "Security",
          level: "low",
          description: "Military presence provides enhanced security.",
        },
        {
          name: "Weather",
          level: "low",
          description: "Favorable conditions.",
        },
        {
          name: "Labor",
          level: "low",
          description: "Strong workforce stability.",
        },
      ],
    },
  },
  "savannah": {
    id: "savannah",
    name: "Port of Savannah",
    location: "Savannah, Georgia",
    coordinates: "32.07° N - 32.10° N, 81.12° W - 81.07° W",
    satelliteImage: "https://images.unsplash.com/photo-1605731413253-03b530825e7c?w=1200&h=800&fit=crop",
    congestion: {
      level: "low",
      percentage: 34,
      vesselCount: 18,
      avgWaitTime: "1.4 days",
    },
    statistics: {
      annualTEU: "5.9M",
      currentVessels: 18,
      berths: 26,
      craneOperations: 98,
      throughputToday: "8,456 TEU",
      yoyGrowth: "+8.3%",
    },
    news: [
      {
        title: "Fastest-growing major US container port",
        source: "Georgia Ports Authority",
        time: "2h ago",
        category: "operations",
      },
      {
        title: "Harbor deepening project completed",
        source: "Maritime Executive",
        time: "4d ago",
        category: "infrastructure",
      },
    ],
    risks: {
      overall: "low",
      categories: [
        {
          name: "Security",
          level: "low",
          description: "Comprehensive security protocols active.",
        },
        {
          name: "Weather",
          level: "low",
          description: "Hurricane season preparations underway.",
        },
        {
          name: "Labor",
          level: "low",
          description: "Strong workforce availability.",
        },
      ],
    },
  },
  "charleston": {
    id: "charleston",
    name: "Port of Charleston",
    location: "Charleston, South Carolina",
    coordinates: "32.81° N - 32.84° N, 79.96° W - 79.91° W",
    satelliteImage: "https://images.unsplash.com/photo-1605731413641-3b3b6e5c3c8f?w=1200&h=800&fit=crop",
    congestion: {
      level: "low",
      percentage: 42,
      vesselCount: 20,
      avgWaitTime: "2.0 days",
    },
    statistics: {
      annualTEU: "2.6M",
      currentVessels: 20,
      berths: 22,
      craneOperations: 64,
      throughputToday: "5,234 TEU",
      yoyGrowth: "+5.8%",
    },
    news: [
      {
        title: "Southeast trade hub expands capacity",
        source: "South Carolina Ports Authority",
        time: "3h ago",
        category: "operations",
      },
      {
        title: "New rail terminal opens",
        source: "JOC.com",
        time: "2d ago",
        category: "infrastructure",
      },
    ],
    risks: {
      overall: "low",
      categories: [
        {
          name: "Security",
          level: "low",
          description: "Standard security measures active.",
        },
        {
          name: "Weather",
          level: "low",
          description: "Seasonal weather monitoring in place.",
        },
        {
          name: "Labor",
          level: "low",
          description: "Cooperative labor relations.",
        },
      ],
    },
  },
};
