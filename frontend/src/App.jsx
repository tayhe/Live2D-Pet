import { useRef, useEffect, useState } from 'react'
import Live2DDisplay from './components/Live2DModel'
import DialogueBox from './components/DialogueBox'
import { createWsConnection } from './api/ws'
import './App.css'

function App() {
  const live2dRef = useRef(null)
  const wsRef = useRef(null)
  const [connected, setConnected] = useState(false)

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
    return () => conn.disconnect()
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
    </div>
  )
}

export default App
