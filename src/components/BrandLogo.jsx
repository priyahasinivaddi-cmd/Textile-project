function BrandLogo({ compact = false, className = "" }) {
  return (
    <div className={`brand-lockup ${compact ? "brand-lockup--compact" : ""} ${className}`} aria-label="ReWeave Circular Intelligence">
      <svg className="brand-mark" viewBox="0 0 96 96" role="img" aria-hidden="true">
        <defs><linearGradient id="brand-gradient" x1="12" y1="10" x2="82" y2="88" gradientUnits="userSpaceOnUse"><stop stopColor="#22d3ee"/><stop offset=".52" stopColor="#10b981"/><stop offset="1" stopColor="#84cc16"/></linearGradient></defs>
        <path className="brand-thread brand-thread--one" d="M24 31C33 13 59 9 74 24c14 14 12 37-3 49-14 12-36 10-48-4" />
        <path className="brand-thread brand-thread--two" d="M22 69c-10-17-3-40 15-48 18-8 39 2 45 21 5 17-5 36-22 42" />
        <path className="brand-leaf" d="M29 53c13-1 24 5 29 19-14 1-25-5-29-19Zm38-18c-12 2-20 9-22 22 13-2 21-9 22-22Z" />
        <circle cx="48" cy="48" r="7" fill="white" />
      </svg>
      {!compact && <span><strong>ReWeave</strong><small>Circular Intelligence</small></span>}
    </div>
  );
}

export default BrandLogo;
