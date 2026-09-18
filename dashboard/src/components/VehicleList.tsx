import type { Vehicle } from "../types";

interface VehicleListProps {
  vehicles: Vehicle[];
  onSelectFault: (vehicle: Vehicle) => void;
}

export function VehicleList({ vehicles, onSelectFault }: VehicleListProps) {
  if (vehicles.length === 0) {
    return <p className="empty-message">No vehicles are reporting telemetry yet.</p>;
  }

  return (
    <div className="vehicle-list-scroll">
      <table className="vehicle-table">
        <thead>
          <tr>
            <th>Vehicle</th>
            <th>Speed</th>
            <th>Battery</th>
            <th>Firmware</th>
            <th>Fault</th>
          </tr>
        </thead>
        <tbody>
          {vehicles.map((vehicle) => (
            <tr key={vehicle.vehicle_id} className={vehicle.fault_code ? "row-fault" : ""}>
              <td>{vehicle.vehicle_id}</td>
              <td>{vehicle.speed.toFixed(0)} km/h</td>
              <td>{vehicle.battery_percent.toFixed(0)}%</td>
              <td>{vehicle.firmware_version}</td>
              <td>
                {vehicle.fault_code ? (
                  <button className="fault-button" onClick={() => onSelectFault(vehicle)}>
                    {vehicle.fault_code}
                  </button>
                ) : (
                  <span className="no-fault">none</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
