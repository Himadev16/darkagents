import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DARKAGENTS - AI-Powered SaaS Builder",
  description: "Watch AI agents build production-ready SaaS applications in real-time",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
