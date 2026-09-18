import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { Vehicle } from "../types";

const DEFAULT_CENTER: [number, number] = [37.77, -122.42];

const okIcon = L.divIcon({
  className: "vehicle-marker vehicle-marker-ok",
  iconSize: [14, 14],
});

const faultIcon = L.divIcon({
  className: "vehicle-marker vehicle-marker-fault",
  iconSize: [16, 16],
});

interface FleetMapProps {
  vehicles: Vehicle[];
}

export function FleetMap({ vehicles }: FleetMapProps) {
  const center: [number, number] =
    vehicles.length > 0 ? [vehicles[0].latitude, vehicles[0].longitude] : DEFAULT_CENTER;

  return (
    <MapContainer center={center} zoom={12} className="fleet-map" scrollWheelZoom={true}>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {vehicles.map((vehicle) => (
        <Marker
          key={vehicle.vehicle_id}
          position={[vehicle.latitude, vehicle.longitude]}
          icon={vehicle.fault_code ? faultIcon : okIcon}
        >
          <Popup>
            <strong>{vehicle.vehicle_id}</strong>
            <br />
            Speed: {vehicle.speed.toFixed(0)} km/h
            <br />
            Battery: {vehicle.battery_percent.toFixed(0)}%
            <br />
            Firmware: {vehicle.firmware_version}
            <br />
            {vehicle.fault_code ? `Fault: ${vehicle.fault_code}` : "No active fault"}
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
