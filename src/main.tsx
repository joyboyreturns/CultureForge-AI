import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import { StudioBoundary } from './components/StudioBoundary'
import './styles.css'
import './readability.css'
import './wildroot.css'
import './dusk.css'
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><StudioBoundary><App /></StudioBoundary></React.StrictMode>)
