import { useEffect, useState } from "react";
import BrandLogo from "./BrandLogo";

function LoginIntro({ name, onComplete }) {
  const [leaving, setLeaving] = useState(false);

  useEffect(() => {
    const leaveTimer = window.setTimeout(() => setLeaving(true), 3300);
    const completeTimer = window.setTimeout(onComplete, 4000);
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
      </div>
    </div>
  );
}

export default LoginIntro;
