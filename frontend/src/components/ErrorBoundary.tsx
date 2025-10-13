import { Component, ReactNode } from 'react'
import '../styles/components/ErrorBoundary.css'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null
    }
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error
    }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
  }

  handleReset = () => {
    // Reset error state to try rendering again
    this.setState({
      hasError: false,
      error: null
    })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary-page">
          <div className="error-boundary-card">
            <h1>Something went wrong</h1>
            <p className="error-message">
              The application encountered an unexpected error.
            </p>
            {this.state.error && (
              <details className="error-details">
                <summary>Error details</summary>
                <pre>{this.state.error.toString()}</pre>
              </details>
            )}
            <button onClick={this.handleReset} className="btn btn-primary">
              Try Again
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
