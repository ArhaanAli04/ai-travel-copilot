/**
 * Error Boundary Component
 * Catches React errors and displays fallback UI
 */

import React, { Component, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error Boundary caught error:', error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen bg-gradient-to-b from-[#05070a] to-[#0b1120] flex items-center justify-center p-6">
          <div className="max-w-md w-full bg-[#1F2937]/50 backdrop-blur-xl border border-[rgba(148,163,184,0.2)] rounded-2xl p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-full bg-[#EF4444]/10 flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-[#EF4444]" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-white">Something went wrong</h2>
                <p className="text-sm text-[#9CA3AF]">We're working on fixing this</p>
              </div>
            </div>

            {this.state.error && (
              <div className="mb-6 p-4 bg-[#1F2937] rounded-lg border border-[rgba(148,163,184,0.2)]">
                <p className="text-sm font-mono text-[#EF4444] mb-2">
                  {this.state.error.toString()}
                </p>
                {this.state.errorInfo && (
                  <details className="mt-2">
                    <summary className="text-xs text-[#9CA3AF] cursor-pointer hover:text-white">
                      Show details
                    </summary>
                    <pre className="text-xs text-[#9CA3AF] mt-2 overflow-x-auto">
                      {this.state.errorInfo.componentStack}
                    </pre>
                  </details>
                )}
              </div>
            )}

            <button
              onClick={this.handleReset}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-[#F97316] to-[#38BDF8] text-white rounded-lg hover:from-[#EA580C] hover:to-[#3B82F6] transition-all shadow-lg"
            >
              <RefreshCw className="w-4 h-4" />
              Reload Page
            </button>

            <p className="text-xs text-center text-[#6B7280] mt-4">
              If this problem persists, please contact support
            </p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
