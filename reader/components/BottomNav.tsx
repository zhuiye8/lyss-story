"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const tabs = [
  { href: "/", icon: "auto_stories", label: "书架" },
  { href: "/discover", icon: "explore", label: "发现" },
  { href: "/profile", icon: "person", label: "我的" },
];

export default function BottomNav() {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 lg:hidden">
      <div className="flex justify-around items-center px-4 pt-3 pb-safe bg-surface/80 backdrop-blur-2xl shadow-[0_-10px_40px_rgba(0,0,0,0.2)] dark:shadow-[0_-10px_40px_rgba(0,0,0,0.4)] rounded-t-2xl">
        {tabs.map((tab) => {
          const active = isActive(tab.href);
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={`flex flex-col items-center justify-center py-1 px-5 rounded-full transition-all duration-300 ${
                active
                  ? "text-primary bg-primary-container/30"
                  : "text-on-surface-variant/60 hover:text-on-surface-variant"
              }`}
            >
              <span
                className="material-symbols-outlined text-[22px]"
                style={{
                  fontVariationSettings: active
                    ? "'FILL' 1, 'wght' 400"
                    : "'FILL' 0, 'wght' 300",
                }}
              >
                {tab.icon}
              </span>
              <span className="text-[11px] font-label tracking-widest mt-0.5">
                {tab.label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
