const WS_PORT = 10086
const WS_URL = `ws://${window.location.hostname}:${WS_PORT}`

export function createWsConnection(handlers = {}) {
  let ws = null
  let reconnectTimer = null

  function connect() {
    if (ws) return
    ws = new WebSocket(WS_URL)

    ws.onopen = () => {
      console.log("[WS] Connected to push server")
      handlers.onConnect?.()
      // Send a test log to verify log forwarding works
      const testMsg = JSON.stringify({ type: 'client_log', level: 'log', message: '[WS] Log forwarding active at ' + new Date().toISOString() })
      ws.send(testMsg)
      console.log('[WS] Test log sent')
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        console.log('[WS] Received:', data.type, data)
        handleMessage(data)
      } catch (e) {
        console.warn("[WS] Parse error:", e)
      }
    }

    ws.onclose = () => {
      console.log("[WS] Disconnected, reconnecting in 2s...")
      ws = null
      handlers.onDisconnect?.()
      reconnectTimer = setTimeout(connect, 2000)
    }

    ws.onerror = (err) => {
      console.error("[WS] Error:", err)
    }
  }

  function handleMessage(data) {
    switch (data.type) {
      case "display_text":
        handlers.onDisplayText?.(data.text, data.duration, data.model)
        break
      case "set_expression":
        handlers.onSetExpression?.(data.exp_id, data.model)
        break
      case "clear_expression":
        handlers.onClearExpression?.(data.model)
        break
      case "trigger_motion":
        handlers.onTriggerMotion?.(data.motion, data.model)
        break
      case "set_position":
        handlers.onSetPosition?.(data.x, data.y, data.model)
        break
      case "set_effect":
        handlers.onSetEffect?.(data.effect_id)
        break
      case "set_mouth_open":
        handlers.onSetMouthOpen?.(data.value)
        break
      case "quick_replies":
        handlers.onQuickReplies?.(data.options)
        break
      case "reload":
        window.location.reload()
        break
      default:
        console.warn("[WS] Unknown message type:", data.type)
    }
  }

  connect()

  return {
    disconnect() {
      clearTimeout(reconnectTimer)
      if (ws) {
        ws.close()
        ws = null
      }
    },
    send(data) {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(data))
      }
    },
    sendLog(level, ...args) {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'client_log', level, message: args.map(String).join(' ') }))
      }
    },
  }
}
