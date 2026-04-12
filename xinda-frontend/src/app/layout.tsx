import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "外文档案文献处理工作台",
  description: "外文档案文献 OCR 识别与翻译（项目代号 xinda）",
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" className="h-full antialiased">
      <body className="min-h-full flex flex-col" style={{ backgroundColor: '#faf8f2' }}>{children}</body>
    </html>
  );
}
