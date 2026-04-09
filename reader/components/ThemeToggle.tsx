"use client";

import { useEffect, useState } from "react";

export default function ThemeToggle() {
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    const saved = localStorage.getItem("reader-theme");
    if (saved === "light") {
      setIsDark(false);
      document.documentElement.classList.remove("dark");
    }
  }, []);

  const toggle = () => {
    const next = !isDark;
    setIsDark(next);
    if (next) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("reader-theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("reader-theme", "light");
    }
  };

  return (
    <button
      onClick={toggle}
      className="p-2 rounded-lg hover:bg-gray-800 dark:hover:bg-gray-700 transition text-gray-400"
      title={isDark ? "切换到亮色模式" : "切换到暗色模式"}
    >
      {isDark ? "☀" : "☾"}
    </button>
  );
}
