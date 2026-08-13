import { NavLink } from "react-router-dom";

import type { UserRole } from "types/models";

interface SidebarItem {
  label: string;
  to: string;
}

interface SidebarProps {
  isOpen: boolean;
  onNavigate: () => void;
  role: UserRole;
}

const riderItems: SidebarItem[] = [
  { label: "Dashboard", to: "/rider/dashboard" },
  { label: "Request Ride", to: "/rider/request-ride" },
  { label: "Current Ride", to: "/rider/current-ride" },
  { label: "Ride History", to: "/rider/history" }
];

const driverItems: SidebarItem[] = [
  { label: "Dashboard", to: "/driver/dashboard" },
  { label: "Availability", to: "/driver/availability" },
  { label: "Current Trip", to: "/driver/current-trip" },
  { label: "Completed Trips", to: "/driver/history" }
];

const supportItems: SidebarItem[] = [
  { label: "Support Cases", to: "/support/cases" }
];

const operationsItems: SidebarItem[] = [{ label: "Operations Dashboard", to: "/operations/dashboard" }];

function getItemsForRole(role: UserRole): SidebarItem[] {
  switch (role) {
    case "RIDER":
      return riderItems;
    case "DRIVER":
      return driverItems;
    case "SUPPORT_AGENT":
    case "PAYMENT_AGENT":
      return supportItems;
    case "OPERATIONS_MANAGER":
    case "ADMIN":
      return operationsItems;
    default:
      return [];
  }
}

export function Sidebar({ isOpen, onNavigate, role }: SidebarProps) {
  const items = getItemsForRole(role);

  return (
    <aside className={`sidebar ${isOpen ? "sidebar--open" : ""}`}>
      <nav>
        <p className="sidebar__title">Workspace</p>
        <ul className="sidebar__list">
          {items.map((item) => (
            <li key={item.to}>
              <NavLink
                className={({ isActive }) => `sidebar__link ${isActive ? "sidebar__link--active" : ""}`}
                onClick={onNavigate}
                to={item.to}
              >
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
