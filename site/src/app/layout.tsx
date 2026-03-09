import type { Metadata } from "next";
import { Instrument_Serif, DM_Mono } from "next/font/google";
import localFont from "next/font/local";
import { Nav } from "@/components/Nav";
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
  title: "Gravity Stack — AI-Native Dev Environment",
  description:
    "The complete blueprint for a top 1% AI-native development environment. 31 plugins, 9+3 MCP servers, 7 hooks, 53 skills.",
  openGraph: {
    title: "Gravity Stack",
    description: "The complete blueprint for a top 1% AI-native development environment.",
    type: "website",
  },
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
        <main>{children}</main>
      </body>
    </html>
  );
}
