import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Story Engine - AI小说生成系统",
  description: "多智能体协作的AI中文长篇小说生成系统",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="zh-CN"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <nav className="border-b bg-white">
          <div className="max-w-6xl mx-auto px-8 py-3 flex items-center justify-between">
            <a href="/" className="font-bold text-lg">Story Engine</a>
            <div className="flex gap-4 text-sm">
              <a href="/" className="text-gray-600 hover:text-black">首页</a>
              <a href="/admin" className="text-gray-600 hover:text-black">管理中心</a>
              <a href="/admin/logs" className="text-gray-600 hover:text-black">请求日志</a>
            </div>
          </div>
        </nav>
        {children}
      </body>
    </html>
  );
}
