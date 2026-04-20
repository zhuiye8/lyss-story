import Image from "next/image";
import { cn } from "@/lib/utils";

export type MascotVariant = "cheering" | "heart-love" | "thumbs-up" | "sad-pleading";

const MAP: Record<MascotVariant, string> = {
  cheering: "/mascot/lymo-cheering.png",
  "heart-love": "/mascot/lymo-heart-love.png",
  "thumbs-up": "/mascot/lymo-thumbs-up.png",
  "sad-pleading": "/mascot/lymo-sad-pleading.png",
};

interface MascotProps {
  variant?: MascotVariant;
  size?: number;
  className?: string;
  priority?: boolean;
}

export function Mascot({
  variant = "cheering",
  size = 120,
  className,
  priority = false,
}: MascotProps) {
  return (
    <Image
      src={MAP[variant]}
      alt="Lymo 狸梦"
      width={size}
      height={size}
      priority={priority}
      className={cn("select-none drop-shadow-2xl", className)}
    />
  );
}
