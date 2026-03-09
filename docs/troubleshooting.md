# Troubleshooting

Common issues with Claude Code, Gravity Stack tooling, and the development environment. Each entry includes symptoms, cause, and fix.

---

## claude: command not found

**Symptoms**: Running `claude` in the terminal returns "command not found" or "zsh: command not found: claude".

**Cause**: The Claude Code CLI is not installed or not in your PATH.

**Fix**:

1. Install Claude Code:
   ```bash
   npm install -g @anthropic/claude-code
   ```

2. If already installed, check that your npm global bin is in PATH:
   ```bash
   npm bin -g
   ```

3. Add the output path to your shell profile (`~/.zshrc` or `~/.bashrc`):
   ```bash
   export PATH="$PATH:$(npm bin -g)"
   ```

4. Reload your shell:
   ```bash
   source ~/.zshrc
   ```

---

## MCP Server Timeout

**Symptoms**: Claude Code hangs on startup or shows "MCP server failed to connect" errors. Tools from a specific MCP server are unavailable.

**Cause**: The MCP server process failed to start, crashed, or the connection timed out. Common with SSE servers that are not running.

**Fix**:

1. Check if the server is running (for SSE servers):
   ```bash
   # Obsidian
   curl -s http://localhost:22360/sse

   # Crawl4AI
   curl -s http://localhost:11235/sse
   ```

2. For npm servers, verify the package is installed:
   ```bash
   npx @anthropic/mcp-playwright --version
   ```

3. Check your `settings.json` for typos in the server config.

4. Try running the server manually to see error output:
   ```bash
   npx @anthropic/mcp-playwright
   ```

5. If a server consistently fails, temporarily remove it from `settings.json` and restart Claude Code. Add it back after resolving the issue.

6. For API-dependent servers (Firecrawl, Perplexity), verify your API key is valid and not expired.

---

## Hook Permission Denied

**Symptoms**: Hook fails with "permission denied" error. Claude Code shows the hook command but it does not execute.

**Cause**: The hook script file does not have execute permissions, or the command references a script that is not executable.

**Fix**:

1. If the hook references a script file, make it executable:
   ```bash
   chmod +x ~/.claude/hooks/my-hook.sh
   ```

2. If the hook uses `node -e` or `python3`, verify those commands work in your terminal:
   ```bash
   node -e "console.log('ok')"
   python3 -c "print('ok')"
   ```

3. Check that the hook command in `settings.json` does not have unescaped special characters. JSON requires escaping backslashes and quotes.

4. Test the hook manually:
   ```bash
   MCP_TOOL_INPUT_FILE_PATH="test.ts" node -e "console.log(process.env.MCP_TOOL_INPUT_FILE_PATH)"
   ```

---

## Node Version Mismatch

**Symptoms**: Build errors mentioning unsupported syntax, missing APIs, or "SyntaxError: Unexpected token". Some packages fail to install.

**Cause**: Your Node.js version is too old for the project dependencies. Next.js 16 requires Node.js 18.18.0 or later.

**Fix**:

1. Check your current version:
   ```bash
   node --version
   ```

2. Install the correct version with nvm:
   ```bash
   nvm install 22
   nvm use 22
   nvm alias default 22
   ```

3. Or with Homebrew:
   ```bash
   brew install node@22
   ```

4. Verify after installation:
   ```bash
   node --version  # Should be 22.x
   ```

5. Reinstall dependencies after switching versions:
   ```bash
   rm -rf node_modules
   npm install
   ```

---

## TypeScript Build Errors

**Symptoms**: `tsc --noEmit` reports errors. Build fails with type errors. The Commit Gate hook blocks commits.

**Cause**: Type errors in the codebase. Common after refactoring, adding new dependencies, or when types are not synchronized.

**Fix**:

1. Run the type checker to see all errors:
   ```bash
   npx tsc --noEmit
   ```

2. Common error patterns and solutions:

   **Missing types for a dependency**:
   ```bash
   npm install -D @types/package-name
   ```

   **Property does not exist on type**:
   Check that your interfaces/types are up to date with your data structures.

   **Cannot find module**:
   ```bash
   # Check tsconfig.json paths
   # Verify the import path is correct
   # Ensure the file exists
   ```

   **Type 'X' is not assignable to type 'Y'**:
   Review the type definitions. Often caused by optional vs required fields or union types.

3. If the Commit Gate hook is blocking and you need to commit urgently, fix the type errors first. The hook exists to prevent broken commits.

---

## Missing Font Files

**Symptoms**: Text renders in a fallback system font instead of Satoshi. Console shows 404 errors for font files. `next/font` throws a "Could not load font" error.

**Cause**: Satoshi font files are not in the expected location. Unlike Instrument Serif and DM Mono (loaded from Google Fonts), Satoshi must be self-hosted.

**Fix**:

1. Download Satoshi from [fontshare.com](https://www.fontshare.com/fonts/satoshi).

2. Place the WOFF2 files in `/public/fonts/`:
   ```
   public/
     fonts/
       Satoshi-Regular.woff2
       Satoshi-Medium.woff2
       Satoshi-Bold.woff2
   ```

3. Verify your `next/font/local` configuration in `app/layout.tsx` matches the file paths:
   ```typescript
   const body = localFont({
     src: [
       { path: "../public/fonts/Satoshi-Regular.woff2", weight: "400" },
       { path: "../public/fonts/Satoshi-Medium.woff2", weight: "500" },
       { path: "../public/fonts/Satoshi-Bold.woff2", weight: "700" },
     ],
     variable: "--font-body",
   });
   ```

4. Restart the dev server after adding fonts:
   ```bash
   npm run dev
   ```

---

## Tailwind v4 @theme Syntax Errors

**Symptoms**: Tailwind utility classes do not work. Custom colors/spacing defined in `@theme` are not recognized. Build warnings about unknown at-rules.

**Cause**: Tailwind v4 uses a CSS-based configuration with `@theme` blocks instead of the `tailwind.config.ts` file used in v3. Mixing v3 and v4 syntax causes errors.

**Fix**:

1. Verify you are using Tailwind v4:
   ```bash
   npx tailwindcss --version  # Should be 4.x
   ```

2. Remove `tailwind.config.ts` if it exists. Tailwind v4 does not use it.

3. Define your theme in your global CSS file (e.g., `app/globals.css`):
   ```css
   @import "tailwindcss";

   @theme {
     --color-electric: #00d4ff;
     --color-volt: #b8ff00;
     /* ... */
   }
   ```

4. Do NOT use the v3 `theme.extend` syntax:
   ```javascript
   // WRONG (v3 syntax)
   module.exports = {
     theme: { extend: { colors: { electric: "#00d4ff" } } }
   }
   ```

5. Use the custom colors with standard Tailwind classes:
   ```html
   <div class="text-electric bg-s1 border-border">
   ```

6. If your IDE shows `@theme` as an unknown at-rule, install the Tailwind CSS IntelliSense VS Code extension (v4 compatible).

---

## Missing shadcn/ui Component Imports

**Symptoms**: Build error "Module not found: Can't resolve '@/components/ui/button'" or similar. Components render as undefined.

**Cause**: The shadcn/ui component has not been added to the project. shadcn/ui does not install all components at once -- each must be added individually.

**Fix**:

1. Add the missing component:
   ```bash
   npx shadcn@latest add button
   npx shadcn@latest add card
   npx shadcn@latest add dialog
   ```

2. To see all available components:
   ```bash
   npx shadcn@latest add
   ```

3. Verify the component exists in your project:
   ```bash
   ls src/components/ui/
   ```

4. Check that your `tsconfig.json` has the `@/` path alias configured:
   ```json
   {
     "compilerOptions": {
       "paths": {
         "@/*": ["./src/*"]
       }
     }
   }
   ```

5. If you initialized shadcn/ui with a different prefix, adjust your imports accordingly.

---

## Plugin Installation Issues

**Symptoms**: A plugin does not appear in the session. Slash commands from the plugin are not available. `settings.json` shows the plugin but it is not loading.

**Cause**: Plugin name typo, incompatible version, or plugin was removed from the marketplace.

**Fix**:

1. Verify the plugin name in `settings.json` is correct. Names are case-sensitive and use kebab-case.

2. Check plugin status:
   ```
   /plugins status
   ```

3. Re-install the plugin:
   ```
   /plugins
   ```
   Search for the plugin and reinstall it.

4. If the plugin was recently updated and is now broken, check the plugin's GitHub repo for known issues.

5. Remove the plugin from `settings.json` temporarily to confirm it is causing the issue:
   ```json
   {
     "enabledPlugins": [
       // "problematic-plugin",  <-- comment out
     ]
   }
   ```

6. Restart Claude Code after making changes to `settings.json`.

---

## CARL Hook Not Triggering

**Symptoms**: Claude does not mention context brackets. No `<carl-rules>` blocks appear in Claude's responses. Claude behaves the same regardless of context usage.

**Cause**: The CARL engine script is not found, has a Python error, or the `UserPromptSubmit` hook is misconfigured.

**Fix**:

1. Verify the CARL engine file exists:
   ```bash
   ls -la ~/.claude/carl/carl_engine.py
   ```

2. Run it manually to check for errors:
   ```bash
   python3 ~/.claude/carl/carl_engine.py
   ```

3. Check Python version (CARL requires Python 3.8+):
   ```bash
   python3 --version
   ```

4. Verify the hook is configured in `settings.json`:
   ```json
   {
     "hooks": {
       "UserPromptSubmit": [
         {
           "type": "command",
           "command": "python3 ~/.claude/carl/carl_engine.py"
         }
       ]
     }
   }
   ```

5. Check that the CARL manifest exists:
   ```bash
   ls -la ~/.claude/carl/carl_manifest.yaml
   ```

6. If CARL was recently updated, check `carl_state.json` for corruption:
   ```bash
   cat ~/.claude/carl/carl_state.json
   ```
   If malformed, delete it and let CARL regenerate it:
   ```bash
   rm ~/.claude/carl/carl_state.json
   ```

7. Restart Claude Code after fixing the issue. CARL hooks only load on session start.
