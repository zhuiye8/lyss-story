"use client";

import Image from "next/image";
import TopBar from "@/components/TopBar";
import ThemeToggle from "@/components/ThemeToggle";

export default function ProfilePage() {
  return (
    <>
      <TopBar showLogo showSearch />

      <main className="max-w-2xl mx-auto px-4 sm:px-6 py-6">
        {/* Avatar section */}
        <div className="flex flex-col items-center py-8">
          <div className="w-20 h-20 rounded-full bg-surface-container-high flex items-center justify-center mb-4">
            <span className="material-symbols-outlined text-4xl text-on-surface-variant/40">
              person
            </span>
          </div>
          <h2 className="font-headline text-xl font-bold">读者</h2>
          <p className="text-sm text-on-surface-variant/60 mt-1 font-label">
            与狸灵共梦
          </p>
        </div>

        {/* Stats placeholder */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          {[
            { label: "在读", value: "—" },
            { label: "已读", value: "—" },
            { label: "书架", value: "—" },
          ].map((stat) => (
            <div
              key={stat.label}
              className="text-center p-4 bg-surface-container-low rounded-xl"
            >
              <p className="font-headline text-2xl font-bold text-primary">
                {stat.value}
              </p>
              <p className="text-xs text-on-surface-variant/60 font-label mt-1">
                {stat.label}
              </p>
            </div>
          ))}
        </div>

        {/* Settings list */}
        <div className="space-y-1">
          <h3 className="text-xs font-label text-on-surface-variant/50 uppercase tracking-widest mb-3 px-1">
            设置
          </h3>

          <ThemeToggle />

          {[
            { icon: "text_fields", label: "阅读偏好" },
            { icon: "notifications", label: "通知设置" },
            { icon: "info", label: "关于狸梦" },
          ].map((item) => (
            <button
              key={item.label}
              className="w-full flex items-center gap-4 px-4 py-3.5 rounded-xl hover:bg-surface-container-low transition-colors"
            >
              <span className="material-symbols-outlined text-on-surface-variant text-xl">
                {item.icon}
              </span>
              <span className="font-body text-sm flex-1 text-left">
                {item.label}
              </span>
              <span className="material-symbols-outlined text-on-surface-variant/30 text-xl">
                chevron_right
              </span>
            </button>
          ))}
        </div>

        {/* Credit */}
        <div className="mt-12 text-center">
          <Image
            src="/mascot/lymo-thumbs-up.png"
            alt="Lymo"
            width={64}
            height={64}
            className="mx-auto mb-3 opacity-60"
          />
          <p className="text-xs text-on-surface-variant/40 font-label">
            Powered by Story Engine
          </p>
          <p className="text-xs text-on-surface-variant/30 font-label mt-0.5">
            by zhuiye
          </p>
        </div>
      </main>
    </>
  );
}
