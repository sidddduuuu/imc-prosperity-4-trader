import type { Metadata } from "next";
import { Manrope, Syne, JetBrains_Mono } from "next/font/google";
import { SiteHeader } from "@/components/SiteHeader";
import { DisclaimerBanner } from "@/components/DisclaimerBanner";
import { AuthProvider } from "@/lib/auth";
import "./globals.css";

const display = Syne({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["500", "600", "700", "800"],
});

const sans = Manrope({
  variable: "--font-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const mono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "Atlas — Every signal. One terminal.",
  description:
    "Production trading terminal: backtest, charts, news, screener, paper trading, alerts, and research.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${display.variable} ${sans.variable} ${mono.variable} antialiased`}>
        <AuthProvider>
          <SiteHeader />
          <main>{children}</main>
          <DisclaimerBanner />
        </AuthProvider>
      </body>
    </html>
  );
}
