import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { HashRouter } from 'react-router-dom';
import ContextApi from './ContextApi/ContextApi.jsx';

createRoot(document.getElementById('root')).render(
  <HashRouter>
    <ContextApi>
      <App />
    </ContextApi>
  </HashRouter>
)
