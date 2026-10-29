import { useState } from 'react'
import type { ReactNode } from 'react'
import { ArrowLeft, ArrowRight, AudioLines, Coffee, Globe2, Layers3, Leaf } from 'lucide-react'
import type { ProjectRequest } from '../contracts'

export function StudioNav({ back, overview, switchIdea, examples }: { back: { label: string; go: () => void }; overview?: () => void; switchIdea: () => void; examples: () => void }) {
  return <nav className="studio-nav" aria-label="Move between ideas">
    <button className="studio-nav-back" onClick={back.go}><ArrowLeft size={14}/> {back.label}</button>
    <span className="studio-nav-spacer"/>
    {overview && <button className="studio-nav-link" onClick={overview}>Overview</button>}
    <button className="studio-nav-link" onClick={examples}>Try another example</button>
    <button className="studio-nav-link is-primary" onClick={switchIdea}>Switch idea <ArrowRight size={13}/></button>
  </nav>
}
export function NavItem({ icon, label, active, onClick, suffix }: { icon: ReactNode; label: string; active: boolean; onClick: () => void; suffix?: string }) {
  return <button className={`nav-item ${active ? 'active' : ''}`} onClick={onClick} aria-current={active ? 'page' : undefined}>{icon}<span>{label}</span>{suffix && <small>{suffix}</small>}</button>
}
export function BusinessIcon({type,size=14}:{type:ProjectRequest['businessType'];size?:number}) { const Icon = {'Food & beverage':Coffee,Retail:Layers3,Hospitality:Globe2,Wellness:Leaf,Entertainment:AudioLines}[type]; return <Icon size={size}/> }
export function Eyebrow({ children }: { children: ReactNode }) { return <div className="eyebrow"><span/>{children}</div> }
export function Button({ children, onClick, variant = 'primary', type = 'button', disabled = false, 'data-tour': tourTarget }: { 'data-tour'?: string; children: ReactNode; onClick?: () => void; variant?: 'primary' | 'secondary' | 'text'; type?: 'button' | 'submit'; disabled?: boolean }) { return <button data-tour={tourTarget} type={type} className={`button button-${variant}`} onClick={onClick} disabled={disabled}>{children}</button> }

export function CopyLink({url}:{url:string}){
  const [state,setState]=useState<'idle'|'copied'|'failed'>('idle')
  async function copy(){
    try { await navigator.clipboard.writeText(url); setState('copied') } catch { setState('failed') }
    window.setTimeout(()=>setState('idle'),2500)
  }
  return <button type="button" className="button button-secondary copy-link" onClick={copy}>{state==='copied'?'Copied':state==='failed'?'Select the link and copy it':'Copy link'}</button>
}
export function BarIcon(){return <svg width="15" height="15" viewBox="0 0 15 15" fill="none" aria-hidden="true"><path d="M2 3h11M2 7.5h11M2 12h11" stroke="currentColor" strokeWidth="1.5"/></svg>}
