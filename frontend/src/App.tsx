import { useState } from 'react'
import { SetupScreen } from './components/SetupScreen'

type AppState =
  | { screen: 'setup' }
  | { screen: 'wizard'; sessionId: string; sections: string[] }

export default function App() {
  const [state, setState] = useState<AppState>({ screen: 'setup' })

  if (state.screen === 'setup') {
    return (
      <SetupScreen
        onSessionStart={(sessionId, sections) =>
          setState({ screen: 'wizard', sessionId, sections })
        }
      />
    )
  }

  // Wizard UI — Milestone 10
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <p className="text-gray-500 text-sm">
        Session <code className="font-mono">{state.sessionId}</code> — wizard coming in Milestone
        10
      </p>
    </div>
  )
}
