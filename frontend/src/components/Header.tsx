import { Button } from "./Button";
import type { User } from "types/models";
import { formatRole } from "utils/app";

interface HeaderProps {
  user: User;
  onMenuToggle: () => void;
  onLogout: () => void;
}

export function Header({ onLogout, onMenuToggle, user }: HeaderProps) {
  return (
    <header className="app-header">
      <div className="app-header__brand">
        <button className="app-header__menu" onClick={onMenuToggle} type="button">
          Menu
        </button>
        <div>
          <span className="app-header__eyebrow">RideSphere Control</span>
          <strong>RideSphere</strong>
        </div>
      </div>
      <div className="app-header__profile">
        <div>
          <strong>
            {user.first_name} {user.last_name}
          </strong>
          <span>{formatRole(user.role)}</span>
        </div>
        <Button onClick={onLogout} type="button" variant="secondary">
          Sign out
        </Button>
      </div>
    </header>
  );
}
