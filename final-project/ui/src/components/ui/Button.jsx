const SIZES = {
  md: "h-12 px-5 text-sm",
  sm: "h-9 px-3.5 text-sm",
  lg: "h-[52px] px-6 text-[15px]",
  icon: "h-10 w-10",
};

const VARIANTS = {
  primary:
    "text-white gradient-primary shadow-glow hover:-translate-y-0.5 hover:shadow-[0_10px_36px_rgba(99,102,241,.45)] active:translate-y-0",
  secondary:
    "bg-white text-ink border border-line shadow-soft hover:-translate-y-0.5 hover:shadow-lift hover:border-slate-300",
  ghost: "text-muted hover:bg-slate-100 hover:text-ink",
  subtle: "bg-slate-100 text-ink hover:bg-slate-200",
};

export default function Button({
  variant = "primary",
  size = "md",
  className = "",
  children,
  ...props
}) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-xl font-semibold
        transition-all duration-200 ease-out focus:outline-none focus-visible:ring-2
        focus-visible:ring-primary/40 disabled:pointer-events-none disabled:opacity-50
        ${SIZES[size]} ${VARIANTS[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
