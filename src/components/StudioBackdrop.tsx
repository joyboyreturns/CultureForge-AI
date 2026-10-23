import { useEffect, useRef } from 'react'
import { startScene } from '../../landing-scene.js'

/**
 * The landing page's dusk, behind the studio.
 *
 * The same scene the front page draws (landing-scene.js), painted once as a
 * still frame and veiled, so the studio reads as the same place without an
 * animation running under every glass panel.
 */
export function StudioBackdrop() {
  const canvas = useRef<HTMLCanvasElement>(null)
  useEffect(() => {
    if (!canvas.current) return
    return startScene(canvas.current, { animate: false })
  }, [])
  return <div className="studio-backdrop" aria-hidden="true">
    <canvas ref={canvas} className="studio-backdrop-scene"/>
    <div className="studio-backdrop-veil"/>
    <div className="studio-backdrop-grain"/>
  </div>
}
