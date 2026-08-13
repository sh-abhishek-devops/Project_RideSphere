export interface LocationArea {
  cityId: string;
  cityName: string;
  areaId: string;
  areaName: string;
  latitude: number;
  longitude: number;
}

export interface LocationCity {
  id: string;
  name: string;
  areas: LocationArea[];
}

export const locationCities: LocationCity[] = [
  {
    id: "new-york-city",
    name: "New York City",
    areas: [
      { cityId: "new-york-city", cityName: "New York City", areaId: "manhattan", areaName: "Manhattan", latitude: 40.7831, longitude: -73.9712 },
      { cityId: "new-york-city", cityName: "New York City", areaId: "brooklyn", areaName: "Brooklyn", latitude: 40.6782, longitude: -73.9442 },
      { cityId: "new-york-city", cityName: "New York City", areaId: "queens", areaName: "Queens", latitude: 40.7282, longitude: -73.7949 },
      { cityId: "new-york-city", cityName: "New York City", areaId: "bronx", areaName: "Bronx", latitude: 40.8448, longitude: -73.8648 },
    ],
  },
  {
    id: "los-angeles",
    name: "Los Angeles",
    areas: [
      { cityId: "los-angeles", cityName: "Los Angeles", areaId: "hollywood", areaName: "Hollywood", latitude: 34.0928, longitude: -118.3287 },
      { cityId: "los-angeles", cityName: "Los Angeles", areaId: "santa-monica", areaName: "Santa Monica", latitude: 34.0195, longitude: -118.4912 },
      { cityId: "los-angeles", cityName: "Los Angeles", areaId: "downtown-la", areaName: "Downtown LA", latitude: 34.0407, longitude: -118.2468 },
      { cityId: "los-angeles", cityName: "Los Angeles", areaId: "venice", areaName: "Venice", latitude: 33.985, longitude: -118.4695 },
    ],
  },
  {
    id: "chicago",
    name: "Chicago",
    areas: [
      { cityId: "chicago", cityName: "Chicago", areaId: "the-loop", areaName: "The Loop", latitude: 41.8837, longitude: -87.6325 },
      { cityId: "chicago", cityName: "Chicago", areaId: "lincoln-park", areaName: "Lincoln Park", latitude: 41.9214, longitude: -87.6513 },
      { cityId: "chicago", cityName: "Chicago", areaId: "wicker-park", areaName: "Wicker Park", latitude: 41.9088, longitude: -87.6795 },
      { cityId: "chicago", cityName: "Chicago", areaId: "hyde-park", areaName: "Hyde Park", latitude: 41.7943, longitude: -87.5907 },
    ],
  },
  {
    id: "houston",
    name: "Houston",
    areas: [
      { cityId: "houston", cityName: "Houston", areaId: "downtown-houston", areaName: "Downtown Houston", latitude: 29.7604, longitude: -95.3698 },
      { cityId: "houston", cityName: "Houston", areaId: "midtown", areaName: "Midtown", latitude: 29.7397, longitude: -95.3776 },
      { cityId: "houston", cityName: "Houston", areaId: "montrose", areaName: "Montrose", latitude: 29.7489, longitude: -95.3909 },
      { cityId: "houston", cityName: "Houston", areaId: "uptown", areaName: "Uptown", latitude: 29.7499, longitude: -95.4613 },
    ],
  },
];

export function getAreasForCity(cityId: string): LocationArea[] {
  return locationCities.find((city) => city.id === cityId)?.areas ?? [];
}

export function getAreaById(cityId: string, areaId: string): LocationArea | null {
  return getAreasForCity(cityId).find((area) => area.areaId === areaId) ?? null;
}

export function formatAreaAddress(area: LocationArea): string {
  return `${area.areaName}, ${area.cityName}`;
}

export function findAreaSelectionByCoordinates(latitude: number, longitude: number): LocationArea {
  const allAreas = locationCities.flatMap((city) => city.areas);
  return (
    allAreas
      .map((area) => ({
        area,
        distance: Math.abs(area.latitude - latitude) + Math.abs(area.longitude - longitude),
      }))
      .sort((left, right) => left.distance - right.distance)[0]?.area ?? allAreas[0]
  );
}

export function haversineKm(latitudeA: number, longitudeA: number, latitudeB: number, longitudeB: number): number {
  const earthRadiusKm = 6371;
  const toRadians = (value: number) => (value * Math.PI) / 180;
  const deltaLat = toRadians(latitudeB - latitudeA);
  const deltaLon = toRadians(longitudeB - longitudeA);
  const latA = toRadians(latitudeA);
  const latB = toRadians(latitudeB);
  const haversine =
    Math.sin(deltaLat / 2) ** 2 +
    Math.cos(latA) * Math.cos(latB) * Math.sin(deltaLon / 2) ** 2;
  return 2 * earthRadiusKm * Math.asin(Math.sqrt(haversine));
}

export function estimateDurationMinutes(distanceKm: number): number {
  const averageCitySpeedKmPerHour = 28;
  return Math.max(6, Math.round((distanceKm / averageCitySpeedKmPerHour) * 60));
}
