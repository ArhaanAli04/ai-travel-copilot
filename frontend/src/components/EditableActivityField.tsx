import { useState, useRef, useEffect } from 'react';
import { Pencil, Check, X, Clock, AlertCircle } from 'lucide-react';

interface EditableActivityFieldProps {
  value: string;
  type: 'text' | 'time';
  onSave: (newValue: string) => Promise<void>;
  placeholder?: string;
  className?: string;
  icon?: React.ReactNode;
  validate?: (value: string) => string | null; // Returns error message or null
}

export const EditableActivityField = ({
  value,
  type,
  onSave,
  placeholder,
  className = '',
  icon,
  validate
}: EditableActivityFieldProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      if (type === 'text') {
        inputRef.current.select();
      }
    }
  }, [isEditing, type]);

  const handleSave = async () => {
    // Validate
    if (validate) {
      const validationError = validate(editValue);
      if (validationError) {
        setError(validationError);
        return;
      }
    }

    // Don't save if unchanged
    if (editValue === value) {
      setIsEditing(false);
      setError(null);
      return;
    }

    setIsSaving(true);
    setError(null);

    try {
      await onSave(editValue);
      setIsEditing(false);
    } catch (err) {
      setError('Failed to save changes');
      console.error('Save error:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setEditValue(value);
    setIsEditing(false);
    setError(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSave();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  };

  if (!isEditing) {
    return (
      <button
        onClick={() => setIsEditing(true)}
        className={`group flex items-center gap-2 hover:bg-white/5 px-2 py-1 rounded-lg transition-all ${className}`}
        title="Click to edit"
      >
        {icon}
        <span>{value || placeholder}</span>
        <Pencil className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity text-[#38BDF8]" />
      </button>
    );
  }

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-2">
        {icon}
        <input
          ref={inputRef}
          type={type}
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={() => {
            // Small delay to allow button clicks to register
            setTimeout(() => {
              if (!isSaving) handleSave();
            }, 150);
          }}
          className={`
            px-2 py-1 rounded-lg bg-[#1F2937] border-2 border-[#38BDF8] 
            text-white focus:outline-none focus:border-[#60A5FA]
            ${type === 'time' ? 'w-24' : 'flex-1'}
            ${error ? 'border-[#EF4444]' : ''}
          `}
          placeholder={placeholder}
          disabled={isSaving}
        />
        
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="p-1 rounded-lg bg-[#22C55E]/20 hover:bg-[#22C55E]/30 text-[#22C55E] disabled:opacity-50 transition-all"
          title="Save"
        >
          {isSaving ? (
            <div className="w-4 h-4 border-2 border-[#22C55E] border-t-transparent rounded-full animate-spin" />
          ) : (
            <Check className="w-4 h-4" />
          )}
        </button>
        
        <button
          onClick={handleCancel}
          disabled={isSaving}
          className="p-1 rounded-lg bg-[#EF4444]/20 hover:bg-[#EF4444]/30 text-[#EF4444] disabled:opacity-50 transition-all"
          title="Cancel"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-1 text-xs text-[#EF4444] ml-6">
          <AlertCircle className="w-3 h-3" />
          {error}
        </div>
      )}
    </div>
  );
};
