import { useState } from 'react'
import { SetupScreen } from './components/SetupScreen'
import { WizardScreen } from './components/WizardScreen'

type AppState =
  | { screen: 'setup' }
  | { screen: 'wizard'; sessionId: string; sections: string[]; resumeLatex: string }
  | { screen: 'review'; sessionId: string }

export default function App() {
  const [state, setState] = useState<AppState>({ screen: 'setup' })

  if (state.screen === 'setup') {
    return (
      <SetupScreen
        onSessionStart={(sessionId, sections, resumeLatex) =>
          setState({ screen: 'wizard', sessionId, sections, resumeLatex })
        }
      />
    )
  }

  if (state.screen === 'wizard') {
    return (
      <WizardScreen
        sessionId={state.sessionId}
        sections={state.sections}
        resumeLatex={state.resumeLatex}
        onReviewReady={(sessionId) => setState({ screen: 'review', sessionId })}
      />
    )
  }

  // Review UI — Milestone 11
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <p className="text-gray-500 text-sm">
        Session <code className="font-mono">{state.sessionId}</code> — review UI coming in
        Milestone 11
      </p>
    </div>
  )
}
