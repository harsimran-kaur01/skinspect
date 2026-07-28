import { useState } from 'react'
import { resendVerification } from '../api/auth'

export default function VerificationBanner({ user }) {
  const [sent, setSent] = useState(false)
  const [sending, setSending] = useState(false)

  if (!user || user.is_verified) return null

  const handleResend = async () => {
    setSending(true)
    try {
      await resendVerification()
      setSent(true)
    } catch {
      // best-effort — banner stays, user can try again
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="bg-amber-50 border border-amber-200 text-amber-800 text-sm px-4 py-3 flex items-center justify-between">
      <span>
        ⚠️ Please verify your email to unlock scanning.
        {sent && ' A new link has been sent — check your inbox.'}
      </span>
      {!sent && (
        <button
          onClick={handleResend}
          disabled={sending}
          className="ml-4 font-medium underline disabled:opacity-50"
        >
          {sending ? 'Sending...' : 'Resend email'}
        </button>
      )}
    </div>
  )
}