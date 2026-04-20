"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Mascot } from "./mascot";
import { ThemeToggle } from "./theme-toggle";
import { cn } from "@/lib/utils";

const LINKS = [
  { href: "/", label: "书斋" },
  { href: "/admin", label: "引擎" },
  { href: "/admin/logs", label: "日志" },
];

export function NavBar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <Mascot variant="thumbs-up" size={28} className="transition-transform group-hover:scale-110" />
          <div className="flex items-baseline gap-1.5">
            <span className="font-serif text-lg font-bold tracking-tight text-gold-grad">狸梦</span>
            <span className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground">Lymo</span>
          </div>
        </Link>

        <div className="flex items-center gap-1">
          <nav className="flex items-center gap-1">
            {LINKS.map((l) => {
              const active =
                l.href === "/" ? pathname === "/" : pathname.startsWith(l.href);
              return (
                <Link
                  key={l.href}
                  href={l.href}
                  className={cn(
                    "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                    active
                      ? "bg-secondary text-foreground"
                      : "text-muted-foreground hover:text-foreground hover:bg-secondary/50"
                  )}
                >
                  {l.label}
                </Link>
              );
            })}
          </nav>
          <div className="w-px h-5 bg-border/60 mx-2" />
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
