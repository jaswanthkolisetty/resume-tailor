import { useState } from 'react'
import { ReviewScreen } from './components/ReviewScreen'
import { SetupScreen } from './components/SetupScreen'
import { WizardScreen } from './components/WizardScreen'

type AppState =
  | { screen: 'setup' }
  | {
      screen: 'wizard'
      sessionId: string
      sections: string[]
      resumeLatex: string
      activeSection?: string
    }
  | { screen: 'review'; sessionId: string; sections: string[]; resumeLatex: string }

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
        initialSection={state.activeSection}
        onReviewReady={(sessionId) =>
          setState({
            screen: 'review',
            sessionId,
            sections: state.sections,
            resumeLatex: state.resumeLatex,
          })
        }
      />
    )
  }

  return (
    <ReviewScreen
      sessionId={state.sessionId}
      sections={state.sections}
      onGoToSection={(sectionTitle) =>
        setState({
          screen: 'wizard',
          sessionId: state.sessionId,
          sections: state.sections,
          resumeLatex: state.resumeLatex,
          activeSection: sectionTitle,
        })
      }
      onBack={() =>
        setState({
          screen: 'wizard',
          sessionId: state.sessionId,
          sections: state.sections,
          resumeLatex: state.resumeLatex,
        })
      }
    />
  )
}
