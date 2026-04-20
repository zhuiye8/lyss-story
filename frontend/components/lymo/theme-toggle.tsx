"use client";

import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";

type Theme = "dark" | "light";
const STORAGE_KEY = "lymo-theme";

function applyTheme(theme: Theme) {
  const html = document.documentElement;
  if (theme === "light") {
    html.classList.add("light");
  } else {
    html.classList.remove("light");
  }
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("dark");
  const [mounted, setMounted] = useState(false);

  // Initialize from localStorage on mount
  useEffect(() => {
    const saved = (typeof window !== "undefined"
      ? (localStorage.getItem(STORAGE_KEY) as Theme | null)
      : null) || "dark";
    setTheme(saved);
    applyTheme(saved);
    setMounted(true);
  }, []);

  const toggle = () => {
    const next: Theme = theme === "dark" ? "light" : "dark";
    setTheme(next);
    applyTheme(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // ignore
    }
  };

  // Avoid flash-of-wrong-theme during SSR hydration
  if (!mounted) {
    return (
      <Button variant="ghost" size="icon" aria-label="切换主题">
        <Moon className="size-4" />
      </Button>
    );
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggle}
      aria-label={theme === "dark" ? "切换到亮色" : "切换到暗色"}
      title={theme === "dark" ? "切到亮色" : "切到暗色"}
    >
      {theme === "dark" ? (
        <Sun className="size-4 text-lymo-gold-400" />
      ) : (
        <Moon className="size-4 text-lymo-stellar-500" />
      )}
    </Button>
  );
}

/**
 * Inline pre-hydration script that sets the `light` class before React mounts,
 * so the page doesn't flash between themes on first paint.
 */
export function ThemeScript() {
  const code = `(function(){try{var t=localStorage.getItem("${STORAGE_KEY}");if(t==="light"){document.documentElement.classList.add("light");}}catch(e){}})();`;
  return <script dangerouslySetInnerHTML={{ __html: code }} />;
}
