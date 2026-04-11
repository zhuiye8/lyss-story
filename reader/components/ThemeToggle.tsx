"use client";

import { useEffect, useState } from "react";

export default function ThemeToggle() {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("reader-theme");
    const isDark = saved ? saved === "dark" : false;
    setDark(isDark);
    document.documentElement.classList.toggle("dark", isDark);
  }, []);

  const toggle = () => {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    localStorage.setItem("reader-theme", next ? "dark" : "light");
  };

  return (
    <button
      onClick={toggle}
      className="w-full flex items-center gap-4 px-4 py-3.5 rounded-xl hover:bg-surface-container-low transition-colors"
    >
      <span className="material-symbols-outlined text-on-surface-variant text-xl">
        {dark ? "dark_mode" : "light_mode"}
      </span>
      <span className="font-body text-sm flex-1 text-left">
        {dark ? "深色模式" : "浅色模式"}
      </span>
      <div
        className={`w-10 h-6 rounded-full p-0.5 transition-colors ${
          dark ? "bg-primary" : "bg-outline-variant"
        }`}
      >
        <div
          className={`w-5 h-5 rounded-full bg-surface shadow transition-transform ${
            dark ? "translate-x-4" : "translate-x-0"
          }`}
        />
      </div>
    </button>
  );
}
