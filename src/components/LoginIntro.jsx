import { useEffect, useState } from "react";
import BrandLogo from "./BrandLogo";

function LoginIntro({ name, onComplete }) {
  const [leaving, setLeaving] = useState(false);

  useEffect(() => {
    const leaveTimer = window.setTimeout(() => setLeaving(true), 1100);
    const completeTimer = window.setTimeout(() => { localStorage.setItem("introSeen", "true"); onComplete(); }, 1500);
    return () => { window.clearTimeout(leaveTimer); window.clearTimeout(completeTimer); };
  }, [onComplete]);

  return (
    <div className={`login-intro ${leaving ? "login-intro--leaving" : ""}`} role="status" aria-live="polite">
      <div className="login-intro__halo" />
      <div className="login-intro__content">
        <BrandLogo />
        <p>Welcome back{name ? `, ${name}` : ""}</p>
        <div className="login-intro__progress"><span /></div>
        <small>Preparing your sustainability workspace</small>
        <button type="button" onClick={() => { localStorage.setItem("introSeen", "true"); onComplete(); }} className="rounded-full bg-white/10 px-4 py-2 text-xs font-bold text-white ring-1 ring-white/20">Skip</button>
      </div>
    </div>
  );
}

export default LoginIntro;
