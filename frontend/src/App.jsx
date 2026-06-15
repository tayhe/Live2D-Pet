import { useRef, useEffect, useState } from 'react'
import Live2DDisplay from './components/Live2DModel'
import DialogueBox from './components/DialogueBox'
import { createWsConnection } from './api/ws'
import './App.css'

function App() {
  const live2dRef = useRef(null)
  const wsRef = useRef(null)
  const [connected, setConnected] = useState(false)
  const [debugLogs, setDebugLogs] = useState([])

  useEffect(() => {
    const conn = createWsConnection({
      onConnect() { setConnected(true) },
      onDisconnect() { setConnected(false) },
      onDisplayText(text, duration) {
        window.__showDialogue?.(text, duration)
      },
      onSetExpression(expId) {
        live2dRef.current?.showExpression(expId)
      },
      onClearExpression() {
        live2dRef.current?.clearExpression()
      },
      onTriggerMotion(motion) {
        live2dRef.current?.triggerMotion(motion)
      },
      onSetPosition(x, y) {
        live2dRef.current?.setPosition(x, y)
      },
      onSetEffect(effectId) {
        console.log('[Effect] TODO:', effectId)
      },
      onSetMouthOpen(value) {
        live2dRef.current?.setMouthOpen(value)
      },
    })
    wsRef.current = conn

    // Intercept console logs for on-screen debug display
    const origLog = console.log
    const origWarn = console.warn
    const origError = console.error
    function addLog(level, args) {
      const msg = args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ')
      setDebugLogs(prev => [...prev.slice(-20), `[${level}] ${msg}`])
    }
    console.log = (...args) => { origLog(...args); addLog('L', args) }
    console.warn = (...args) => { origWarn(...args); addLog('W', args) }
    console.error = (...args) => { origError(...args); addLog('E', args) }

    return () => {
      console.log = origLog
      console.warn = origWarn
      console.error = origError
      conn.disconnect()
    }
  }, [])

  function handleTouch(area, pos) {
    wsRef.current?.send({ type: 'touch', area, x: pos.x, y: pos.y })
  }

  return (
    <div className="app">
      <div className={`ws-status ${connected ? 'on' : 'off'}`} />
      <div className="live2d-main">
        <Live2DDisplay ref={live2dRef} onTouch={handleTouch} />
      </div>
      <DialogueBox />
      <div style={{
        position: 'fixed', bottom: 0, left: 0, right: 0,
        background: 'rgba(0,0,0,0.8)', color: '#0f0', fontSize: 11,
        fontFamily: 'monospace', padding: 4, maxHeight: 150, overflow: 'auto',
        zIndex: 9999
      }}>
        {debugLogs.slice(-10).map((log, i) => <div key={i}>{log}</div>)}
      </div>
    </div>
  )
}

export default App
