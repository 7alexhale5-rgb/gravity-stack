import type { Metadata } from "next";
import { Instrument_Serif, DM_Mono } from "next/font/google";
import localFont from "next/font/local";
import { Nav } from "@/components/Nav";
import { Footer } from "@/components/Footer";
import { SearchDialog } from "@/components/SearchDialog";
import { CursorGlow } from "@/components/CursorGlow";
import "./globals.css";

const instrumentSerif = Instrument_Serif({
  subsets: ["latin"],
  weight: "400",
  variable: "--font-heading",
});

const dmMono = DM_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-mono",
});

const satoshi = localFont({
  src: [
    { path: "../fonts/Satoshi-Regular.woff2", weight: "400" },
    { path: "../fonts/Satoshi-Medium.woff2", weight: "500" },
    { path: "../fonts/Satoshi-Bold.woff2", weight: "700" },
  ],
  variable: "--font-body",
});

export const metadata: Metadata = {
  title: {
    default: "Gravity Stack — AI-Native Dev Environment",
    template: "%s — Gravity Stack",
  },
  description:
    "The complete blueprint for a top 1% AI-native development environment. 31 plugins, 7+3 MCP servers, 7 hooks, 53 skills, CARL governance engine.",
  metadataBase: new URL("https://site-phi-lac-73.vercel.app"),
  openGraph: {
    title: "Gravity Stack",
    description:
      "The complete blueprint for a top 1% AI-native development environment. Open source. Documented. Ready to fork.",
    type: "website",
    siteName: "Gravity Stack",
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
    title: "Gravity Stack",
    description:
      "The complete blueprint for a top 1% AI-native development environment.",
  },
  keywords: [
    "Claude Code",
    "AI development",
    "AI-native",
    "MCP servers",
    "Claude plugins",
    "CARL engine",
    "developer tools",
    "AI coding",
    "development environment",
  ],
  authors: [{ name: "Alex Hale" }],
  creator: "Alex Hale",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${instrumentSerif.variable} ${dmMono.variable} ${satoshi.variable} antialiased`}
      >
        <Nav />
        <main className="min-h-[calc(100vh-3.5rem)]">{children}</main>
        <Footer />
        <SearchDialog />
        <CursorGlow />
      </body>
    </html>
  );
}
