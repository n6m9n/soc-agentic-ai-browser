import { User } from "lucide-react";
import ProfileSettings from "../components/ProfileSettings";

export default function ProfileView() {
  return (
    <div className="space-y-5">
      <header className="flex items-center gap-3">
        <span className="grid h-10 w-10 place-items-center rounded-xl bg-primary/10 text-primary"><User size={18} /></span>
        <div>
          <h1 className="text-xl font-bold tracking-tight text-ink">Profile</h1>
          <p className="text-sm text-muted">What your assistant knows about you.</p>
        </div>
      </header>
      <ProfileSettings />
    </div>
  );
}
