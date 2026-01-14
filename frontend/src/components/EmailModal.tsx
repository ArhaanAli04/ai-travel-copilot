import { X, Mail, Loader, CheckCircle, AlertCircle } from 'lucide-react';
import { useState } from 'react';

interface EmailModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSend: (email: string) => Promise<void>;
  tripTitle: string;
}

const EmailModal = ({ isOpen, onClose, onSend, tripTitle }: EmailModalProps) => {
  const [email, setEmail] = useState('');
  const [sending, setSending] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSending(true);

    try {
      await onSend(email);
      setSuccess(true);
      setTimeout(() => {
        onClose();
        setSuccess(false);
        setEmail('');
      }, 2000);
    } catch (err: any) {
      setError(err.message || 'Failed to send email');
    } finally {
      setSending(false);
    }
  };

  const handleClose = () => {
    if (!sending) {
      onClose();
      setEmail('');
      setError('');
      setSuccess(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="glass-card rounded-2xl max-w-md w-full p-6 border-[rgba(148,163,184,0.2)] animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <Mail className="w-5 h-5 text-[#10B981]" />
            <h2 className="text-xl font-bold text-white">Email Itinerary</h2>
          </div>
          <button
            onClick={handleClose}
            disabled={sending}
            className="p-1 hover:bg-white/10 rounded-lg transition-colors disabled:opacity-50"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Success State */}
        {success ? (
          <div className="text-center py-8">
            <CheckCircle className="w-16 h-16 text-[#10B981] mx-auto mb-4" />
            <p className="text-white font-semibold text-lg mb-2">Email Sent!</p>
            <p className="text-gray-400 text-sm">Check your inbox for the itinerary</p>
          </div>
        ) : (
          <>
            {/* Description */}
            <p className="text-gray-400 text-sm mb-6">
              Send <span className="text-white font-medium">{tripTitle}</span> itinerary to your email with a beautifully formatted PDF attachment.
            </p>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
                  Email Address
                </label>
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  disabled={sending}
                  className="w-full px-4 py-3 bg-white/5 border border-[rgba(148,163,184,0.2)] rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-[#10B981] transition-colors disabled:opacity-50"
                />
              </div>

              {/* Error Message */}
              {error && (
                <div className="flex items-start gap-2 p-3 bg-[#EF4444]/10 border border-[#EF4444]/30 rounded-lg">
                  <AlertCircle className="w-5 h-5 text-[#EF4444] flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-[#FCA5A5]">{error}</p>
                </div>
              )}

              {/* Buttons */}
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={handleClose}
                  disabled={sending}
                  className="flex-1 px-4 py-3 border border-[rgba(148,163,184,0.2)] text-white rounded-xl hover:bg-white/5 transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={sending || !email}
                  className="flex-1 px-4 py-3 bg-[#10B981] text-white rounded-xl hover:bg-[#059669] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-semibold"
                >
                  {sending ? (
                    <>
                      <Loader className="w-4 h-4 animate-spin" />
                      Sending...
                    </>
                  ) : (
                    <>
                      <Mail className="w-4 h-4" />
                      Send Email
                    </>
                  )}
                </button>
              </div>
            </form>

            {/* Info */}
            <p className="text-xs text-gray-500 mt-4 text-center">
              The email will include your complete itinerary with activities, times, and descriptions.
            </p>
          </>
        )}
      </div>
    </div>
  );
};

export default EmailModal;
