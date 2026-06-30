---
description: Restart the dev environment (Vite frontend + MCP backend).
---

## Restart Dev Environment

Restart the Live2D companion dev stack. This is needed because:

1. Vite HMR may not work in some environments — code changes may require manual restart
2. MCP Server caches tool definitions — code changes require kill + restart

### Steps

**1. Restart Vite frontend (port 5173):**

```bash
pkill -f "vite" 2>/dev/null; sleep 1
cd ~/Ai-Companion/live2d-ai-companion/frontend && setsid node node_modules/.bin/vite --host > /tmp/vite.log 2>&1 &
sleep 4
ss -tlnp | grep 5173
curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:5173
```

**2. Restart MCP Server (port 10086):**

```bash
# Kill old server
ps aux | grep "src.server" | grep -v grep | awk '{print $2}' | xargs -r kill 2>/dev/null
sleep 1

# Start new server
cd ~/Ai-Companion/live2d-ai-companion && setsid .venv/bin/python -m src.server > /tmp/backend.log 2>&1 &
sleep 3
ss -tlnp | grep 10086
```

**3. Verify both ports:**

```bash
echo "Frontend (5173): $(curl -s -o /dev/null -w '%{http_code}' http://localhost:5173)"
echo "PushServer (10086): $(ss -tlnp | grep 10086 | wc -l) listeners"
```

### Notes

- Use `setsid` + redirect to `/tmp/*.log` so processes survive shell exit
- Always verify ports with `ss -tlnp` after restart
- If port is still occupied, use `kill -9` as last resort
- Frontend needs to be opened in Chrome (with CDP profile) for browser-based testing
