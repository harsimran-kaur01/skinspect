import { useState } from 'react'
import { resendVerification } from '../api/auth'

export default function VerificationBanner({ user }) {
  const [status, setStatus] = useState('idle') // 'idle' | 'sending' | 'sent' | 'error'

  if (!user || user.is_verified) return null

  const handleResend = async () => {
    setStatus('sending')
    try {
      await resendVerification()
      setStatus('sent')
    } catch {
      setStatus('error')
    }
  }

  return (
    <div className="bg-clay/10 border-b border-clay/30 text-sm text-ink">
      <div className="max-w-5xl mx-auto px-6 py-2 flex items-center justify-between gap-4">
        {status === 'sent' ? (
          <span>Verification email sent — check your inbox.</span>
        ) : (
          <span>Please verify your email address to unlock all features.</span>
        )}

        {status !== 'sent' && (
          <button
            onClick={handleResend}
            disabled={status === 'sending'}
            className="font-medium text-clay hover:underline whitespace-nowrap disabled:opacity-50"
          >
            {status === 'sending' ? 'Sending...' : 'Resend email →'}
          </button>
        )}

        {status === 'error' && (
          <span className="text-red-600">Failed to send — try again.</span>
        )}
      </div>
    </div>
  )
}