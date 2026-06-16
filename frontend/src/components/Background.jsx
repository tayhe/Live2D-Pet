import { useState, useEffect } from 'react'
import { getTimeOfDay } from '../utils/timeOfDay'

export default function Background() {
  const [timeOfDay, setTimeOfDay] = useState(getTimeOfDay)

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeOfDay(getTimeOfDay())
    }, 60000)
    return () => clearInterval(timer)
  }, [])

  return (
    <div className="scene-background">
      {['day', 'evening', 'night'].map(period => (
        <img
          key={period}
          src={`/backgrounds/room-${period}.png`}
          className="scene-bg-img"
          style={{ opacity: timeOfDay === period ? 1 : 0 }}
          alt=""
        />
      ))}
    </div>
  )
}
