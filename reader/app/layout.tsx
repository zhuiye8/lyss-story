import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "书架 — AI长篇小说",
  description: "AI多智能体协作创作的中文长篇小说",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" className="dark h-full antialiased">
      <body className="min-h-full bg-gray-950 text-gray-200">
        {children}
      </body>
    </html>
  );
}
