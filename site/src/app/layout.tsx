import type { Metadata } from "next";
import { Space_Grotesk, JetBrains_Mono } from "next/font/google";
import { Nav } from "@/components/Nav";
import { Footer } from "@/components/Footer";
import { SearchDialog } from "@/components/SearchDialog";
import { ParticleNetwork } from "@/components/ParticleNetwork";
import "./globals.css";

const spaceGroteskHeading = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-heading",
});

const jetBrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});

const spaceGroteskBody = Space_Grotesk({
  subsets: ["latin"],
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
        className={`${spaceGroteskHeading.variable} ${jetBrainsMono.variable} ${spaceGroteskBody.variable} antialiased`}
      >
        <ParticleNetwork />
        <Nav />
        <main className="relative z-[2] min-h-[calc(100vh-3.5rem)]">{children}</main>
        <Footer />
        <SearchDialog />
      </body>
    </html>
  );
}
