"use client";

import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";

interface TopBarProps {
  title?: string;
  subtitle?: string;
  showBack?: boolean;
  backHref?: string;
  showSearch?: boolean;
  showLogo?: boolean;
  transparent?: boolean;
  actions?: React.ReactNode;
}

export default function TopBar({
  title,
  subtitle,
  showBack = false,
  backHref,
  showSearch = false,
  showLogo = false,
  transparent = false,
  actions,
}: TopBarProps) {
  const router = useRouter();
  const pathname = usePathname();

  const navLinks = [
    { href: "/", label: "书架" },
    { href: "/discover", label: "发现" },
    { href: "/profile", label: "我的" },
  ];

  const isNavActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <header
      className={`sticky top-0 z-40 ${
        transparent
          ? "bg-transparent"
          : "bg-surface/80 backdrop-blur-2xl shadow-sm"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-4">
        {/* Left */}
        <div className="flex items-center gap-3 min-w-0">
          {showBack && (
            backHref ? (
              <Link
                href={backHref}
                className="flex-shrink-0 w-9 h-9 flex items-center justify-center rounded-full hover:bg-surface-container-high transition-colors"
              >
                <span className="material-symbols-outlined text-on-surface text-xl">
                  arrow_back
                </span>
              </Link>
            ) : (
              <button
                onClick={() => router.back()}
                className="flex-shrink-0 w-9 h-9 flex items-center justify-center rounded-full hover:bg-surface-container-high transition-colors"
              >
                <span className="material-symbols-outlined text-on-surface text-xl">
                  arrow_back
                </span>
              </button>
            )
          )}
          {showLogo && (
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-2xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                menu_book
              </span>
              <h1 className="font-headline text-xl font-bold italic tracking-tight text-primary">
                狸梦小说
              </h1>
            </div>
          )}
          {/* Desktop nav links */}
          {showLogo && (
            <nav className="hidden lg:flex items-center gap-6 ml-8">
              {navLinks.map((link) => {
                const active = isNavActive(link.href);
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`font-label text-sm tracking-wider pb-0.5 border-b-2 transition-colors ${
                      active
                        ? "text-primary border-primary"
                        : "text-on-surface-variant/60 border-transparent hover:text-on-surface-variant"
                    }`}
                  >
                    {link.label}
                  </Link>
                );
              })}
            </nav>
          )}
          {title && (
            <div className="min-w-0">
              <h1 className="font-headline text-lg font-bold truncate">{title}</h1>
              {subtitle && (
                <p className="text-xs text-on-surface-variant/60 truncate">{subtitle}</p>
              )}
            </div>
          )}
        </div>

        {/* Right */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {showSearch && (
            <button className="w-9 h-9 flex items-center justify-center rounded-full hover:bg-surface-container-high transition-colors">
              <span className="material-symbols-outlined text-on-surface-variant text-xl">
                search
              </span>
            </button>
          )}
          {actions}
        </div>
      </div>
    </header>
  );
}
