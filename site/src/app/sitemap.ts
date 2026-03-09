import type { MetadataRoute } from "next";

const baseUrl = "https://site-phi-lac-73.vercel.app";

export default function sitemap(): MetadataRoute.Sitemap {
  const routes = [
    "",
    "/manifesto",
    "/stack",
    "/plugins",
    "/mcp-servers",
    "/hooks",
    "/carl",
    "/skills",
    "/agents",
    "/architecture",
    "/setup",
    "/roadmap",
  ];

  return routes.map((route) => ({
    url: `${baseUrl}${route}`,
    lastModified: new Date(),
    changeFrequency: route === "" ? "weekly" : "monthly",
    priority: route === "" ? 1 : route === "/setup" ? 0.9 : 0.7,
  }));
}
