import { cn } from "@/lib/utils";

interface CharacterAvatarProps {
  name: string;
  role?: "protagonist" | "antagonist" | "supporting" | string;
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
}

const SIZE: Record<string, string> = {
  sm: "h-8 w-8 text-xs",
  md: "h-12 w-12 text-sm",
  lg: "h-16 w-16 text-base",
  xl: "h-24 w-24 text-2xl",
};

function roleStyles(role?: string): string {
  switch (role) {
    case "protagonist":
      return "bg-gradient-to-br from-lymo-gold-400 to-lymo-gold-600 text-lymo-ink-900 border-lymo-gold-500/60 shadow-[0_0_20px_rgba(212,168,75,0.3)]";
    case "antagonist":
      return "bg-gradient-to-br from-lymo-vermilion-400 to-lymo-vermilion-600 text-white border-lymo-vermilion-500/60 shadow-[0_0_20px_rgba(199,62,58,0.3)]";
    default:
      return "bg-gradient-to-br from-lymo-stellar-400 to-lymo-stellar-600 text-white border-lymo-stellar-500/60";
  }
}

function initials(name: string): string {
  const n = (name || "").trim();
  if (!n) return "·";
  // For Chinese names, take last char (more distinguishing)
  if (/[\u4e00-\u9fa5]/.test(n)) return n.slice(-1);
  const parts = n.split(/\s+/);
  return (parts[0]?.[0] || "") + (parts[1]?.[0] || "");
}

export function CharacterAvatar({
  name,
  role,
  size = "md",
  className,
}: CharacterAvatarProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center justify-center rounded-full border-2 font-serif font-bold select-none",
        SIZE[size],
        roleStyles(role),
        className
      )}
      title={name}
    >
      {initials(name)}
    </div>
  );
}
