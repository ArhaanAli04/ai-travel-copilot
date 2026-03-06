import './globals.css'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { ClerkProvider } from '@clerk/react'
import App from './App.tsx'
import AuthSync from './components/AuthSync.tsx'
const publishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

if (!publishableKey) {
  throw new Error('Missing VITE_CLERK_PUBLISHABLE_KEY')
}
createRoot(document.getElementById('root')!).render(
  <StrictMode>
     <ClerkProvider publishableKey={publishableKey}>
      <App />
       <AuthSync /> 
    </ClerkProvider>
  </StrictMode>,
)
