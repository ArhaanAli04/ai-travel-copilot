import { AlertTriangle, X } from 'lucide-react';

interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  type?: 'danger' | 'warning' | 'info';
  loading?: boolean;
}

const ConfirmModal = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  type = 'danger',
  loading = false,
}: ConfirmModalProps) => {
  if (!isOpen) return null;

  const colors = {
    danger: {
      icon: 'text-[#EF4444]',
      iconBg: 'bg-[#EF4444]/10',
      border: 'border-[#EF4444]/30',
      button: 'bg-[#EF4444] hover:bg-[#DC2626]',
    },
    warning: {
      icon: 'text-[#F59E0B]',
      iconBg: 'bg-[#F59E0B]/10',
      border: 'border-[#F59E0B]/30',
      button: 'bg-[#F59E0B] hover:bg-[#D97706]',
    },
    info: {
      icon: 'text-[#38BDF8]',
      iconBg: 'bg-[#38BDF8]/10',
      border: 'border-[#38BDF8]/30',
      button: 'bg-[#38BDF8] hover:bg-[#0EA5E9]',
    },
  };

  const currentColors = colors[type];

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center animate-fade-in">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative glass-card rounded-3xl p-6 max-w-md w-full mx-4 border-[rgba(148,163,184,0.2)] animate-scale-in">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-xl bg-[#1F2937]/50 hover:bg-[#1F2937] transition-all"
        >
          <X className="w-5 h-5 text-[#9CA3AF]" />
        </button>

        {/* Icon */}
        <div className={`w-14 h-14 rounded-2xl ${currentColors.iconBg} border ${currentColors.border} flex items-center justify-center mb-4`}>
          <AlertTriangle className={`w-7 h-7 ${currentColors.icon}`} />
        </div>

        {/* Title */}
        <h3 className="text-2xl font-bold text-white mb-2">{title}</h3>

        {/* Message */}
        <p className="text-[#9CA3AF] mb-6 leading-relaxed">{message}</p>

        {/* Buttons */}
        <div className="flex gap-3">
          <button
            onClick={onClose}
            disabled={loading}
            className="flex-1 px-6 py-3 rounded-xl font-bold bg-[#1F2937] hover:bg-[#374151] text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className={`flex-1 px-6 py-3 rounded-xl font-bold text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed ${currentColors.button}`}
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Processing...
              </span>
            ) : (
              confirmText
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmModal;
