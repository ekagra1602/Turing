import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgentFlow Voice",
  description: "AI-powered voice assistant with visual feedback",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <></>
      <body style={{ background: 'transparent' }} className="overflow-hidden">{children}</body>
    </html>
  );
}
