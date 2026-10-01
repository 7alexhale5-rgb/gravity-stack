#!/usr/bin/env python3
"""Check actual built HTML, including the JSON users copy from MCP examples."""

from html.parser import HTMLParser
import json
from pathlib import Path


class CodeBlocks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.blocks = []
        self.active = False
        self.text = ""

    def handle_starttag(self, tag, attrs):
        if tag == "pre":
            self.active = True
            self.text = ""

    def handle_data(self, data):
        if self.active:
            self.text += data

    def handle_endtag(self, tag):
        if tag == "pre":
            self.active = False
            self.blocks.append(self.text)


def main():
    page = (
        Path(__file__).resolve().parents[1] / "site/.next/server/app/mcp-servers.html"
    )
    html = page.read_text()
    parser = CodeBlocks()
    parser.feed(html)
    configs = [json.loads(block) for block in parser.blocks]
    assert configs, "No rendered MCP examples were checked"
    assert "~/.claude/settings.json" not in html, "Unsupported MCP destination shown"
    assert html.count(">.mcp.json<") == len(configs), (
        "Project destination missing for an example"
    )
    assert all(config.get("mcpServers") for config in configs), (
        "Missing registration wrapper"
    )
    memories = [
        config["mcpServers"]["memory"]
        for config in configs
        if "memory" in config["mcpServers"]
    ]
    assert len(memories) == 1, "Memory example missing or duplicated"
    assert (
        memories[0]["env"]["MEMORY_FILE_PATH"] == "${HOME}/.claude/memory/graph.json"
    ), "Memory file setting incorrect"
    assert "merge" in html.lower(), "Existing registration merge guidance missing"
    print(
        f"Checked {len(configs)} rendered project MCP examples and Memory configuration"
    )


if __name__ == "__main__":
    main()
