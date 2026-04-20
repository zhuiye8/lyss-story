import type { Metadata } from "next";
import { Inter, Noto_Serif_SC, JetBrains_Mono, Noto_Sans_SC } from "next/font/google";
import { Toaster } from "sonner";
import { NavBar } from "@/components/lymo/nav-bar";
import { ThemeScript } from "@/components/lymo/theme-toggle";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const notoSansSC = Noto_Sans_SC({
  variable: "--font-noto-sans-sc",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

const notoSerifSC = Noto_Serif_SC({
  variable: "--font-noto-serif-sc",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "900"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "狸梦 Lymo · 开启你的小说宇宙",
  description:
    "基于多智能体协作的 AI 中文长篇小说创作平台。世界观、角色、剧情、章节，一体生成。",
  icons: {
    icon: "/mascot/lymo-thumbs-up.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="zh-CN"
      className={`${inter.variable} ${notoSansSC.variable} ${notoSerifSC.variable} ${jetbrainsMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <head>
        <ThemeScript />
      </head>
      <body className="min-h-full flex flex-col bg-background ink-texture">
        <NavBar />
        <main className="flex-1">{children}</main>
        <Toaster
          position="top-right"
          toastOptions={{
            classNames: {
              toast: "bg-card border-border text-foreground",
              description: "text-muted-foreground",
            },
          }}
        />
      </body>
    </html>
  );
}
