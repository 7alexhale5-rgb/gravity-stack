"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";

interface SearchItem {
  title: string;
  description: string;
  href: string;
  category: string;
}

const searchIndex: SearchItem[] = [
  { title: "Home", description: "The Gravity Stack overview", href: "/", category: "Pages" },
  { title: "Manifesto", description: "Why AI-native development matters", href: "/manifesto", category: "Pages" },
  { title: "The Stack", description: "Architecture overview — 3 layers", href: "/stack", category: "Pages" },
  { title: "Plugins", description: "31 verified plugins by category", href: "/plugins", category: "Pages" },
  { title: "MCP Servers", description: "7+3 server constellation", href: "/mcp-servers", category: "Pages" },
  { title: "Hooks", description: "7 lifecycle hooks with code", href: "/hooks", category: "Pages" },
  { title: "CARL Engine", description: "Context Augmentation & Reinforcement Layer", href: "/carl", category: "Pages" },
  { title: "Skills", description: "53 reusable prompt templates", href: "/skills", category: "Pages" },
  { title: "Agent Teams", description: "5 roles with model-tier routing", href: "/agents", category: "Pages" },
  { title: "Architecture", description: "Full system diagram", href: "/architecture", category: "Pages" },
  { title: "Setup Guide", description: "Step-by-step installation", href: "/setup", category: "Pages" },
  { title: "Roadmap", description: "What's planned next", href: "/roadmap", category: "Pages" },
  // Key topics
  { title: "Commit Gate Hook", description: "TypeScript enforcement at commit time", href: "/hooks", category: "Hooks" },
  { title: "File Guard Hook", description: "Protect sensitive files from modification", href: "/hooks", category: "Hooks" },
  { title: "CARL Context Brackets", description: "FRESH, MODERATE, DEPLETED modes", href: "/carl", category: "CARL" },
  { title: "Planning Router", description: "Auto-detect task complexity for planning depth", href: "/carl", category: "CARL" },
  { title: "Playwright MCP", description: "Browser automation server", href: "/mcp-servers", category: "MCP" },
  { title: "Memory MCP", description: "Persistent semantic memory server", href: "/mcp-servers", category: "MCP" },
  { title: "Firecrawl MCP", description: "Web scraping server", href: "/mcp-servers", category: "MCP" },
  { title: "Perplexity MCP", description: "AI-powered web search", href: "/mcp-servers", category: "MCP" },
  { title: "Quick Start", description: "Clone, install, run in minutes", href: "/setup", category: "Setup" },
  { title: "Prerequisites", description: "macOS, Node.js, Python requirements", href: "/setup", category: "Setup" },
  { title: "CLAUDE.md", description: "Project context file for Claude Code", href: "/manifesto", category: "Concepts" },
  { title: "Domain Rules", description: "CARL domain-based rule system", href: "/carl", category: "CARL" },
  { title: "Agent Roles", description: "Architect, Implementer, Researcher, Reviewer, Tester", href: "/agents", category: "Agents" },
];

export function SearchDialog() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const filtered = query.length === 0
    ? searchIndex.slice(0, 8)
    : searchIndex.filter(
        (item) =>
          item.title.toLowerCase().includes(query.toLowerCase()) ||
          item.description.toLowerCase().includes(query.toLowerCase()) ||
          item.category.toLowerCase().includes(query.toLowerCase())
      );

  const navigate = useCallback(
    (href: string) => {
      setOpen(false);
      setQuery("");
      router.push(href);
    },
    [router]
  );

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
      if (e.key === "Escape") {
        setOpen(false);
        setQuery("");
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  useEffect(() => {
    if (open && inputRef.current) {
      inputRef.current.focus();
    }
  }, [open]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((i) => Math.min(i + 1, filtered.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter" && filtered[selectedIndex]) {
      navigate(filtered[selectedIndex].href);
    }
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100]">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-bg/80 backdrop-blur-sm"
        onClick={() => {
          setOpen(false);
          setQuery("");
        }}
      />

      {/* Dialog */}
      <div className="relative max-w-xl mx-auto mt-[15vh] bg-s1 border border-gs-border rounded-xl shadow-2xl overflow-hidden">
        {/* Search input */}
        <div className="flex items-center gap-3 px-4 border-b border-gs-border">
          <svg className="w-4 h-4 text-dim flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
            <path
              fillRule="evenodd"
              d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
              clipRule="evenodd"
            />
          </svg>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search documentation..."
            className="flex-1 py-3 bg-transparent text-text placeholder:text-dim outline-none text-sm"
          />
          <kbd className="hidden md:inline-flex items-center px-1.5 py-0.5 rounded border border-gs-border text-[10px] text-dim font-mono">
            ESC
          </kbd>
        </div>

        {/* Results */}
        <div className="max-h-[50vh] overflow-y-auto p-2">
          {filtered.length === 0 ? (
            <div className="px-4 py-8 text-center text-dim text-sm">
              No results for &ldquo;{query}&rdquo;
            </div>
          ) : (
            filtered.map((item, i) => (
              <button
                key={`${item.href}-${item.title}`}
                onClick={() => navigate(item.href)}
                className={`w-full text-left px-3 py-2.5 rounded-lg flex items-start gap-3 transition-colors ${
                  i === selectedIndex ? "bg-s2" : "hover:bg-s2"
                }`}
              >
                <span className="text-[10px] font-mono text-dim uppercase tracking-wider mt-1 w-12 flex-shrink-0">
                  {item.category}
                </span>
                <div className="min-w-0">
                  <div className="text-sm text-text font-medium truncate">{item.title}</div>
                  <div className="text-xs text-dim truncate">{item.description}</div>
                </div>
              </button>
            ))
          )}
        </div>

        {/* Footer hint */}
        <div className="flex items-center justify-between px-4 py-2 border-t border-gs-border text-[10px] text-dim">
          <div className="flex items-center gap-2">
            <kbd className="px-1 py-0.5 rounded border border-gs-border font-mono">&uarr;&darr;</kbd>
            <span>Navigate</span>
            <kbd className="px-1 py-0.5 rounded border border-gs-border font-mono ml-2">&crarr;</kbd>
            <span>Select</span>
          </div>
          <span>Gravity Stack</span>
        </div>
      </div>
    </div>
  );
}

export function SearchTrigger() {
  return (
    <button
      onClick={() => {
        window.dispatchEvent(
          new KeyboardEvent("keydown", { key: "k", metaKey: true })
        );
      }}
      className="hidden md:inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-gs-border text-xs text-dim hover:text-text hover:border-electric/20 transition-colors"
    >
      <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
        <path
          fillRule="evenodd"
          d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
          clipRule="evenodd"
        />
      </svg>
      Search
      <kbd className="font-mono text-[10px] px-1 py-0.5 rounded border border-gs-border">
        &#8984;K
      </kbd>
    </button>
  );
}
