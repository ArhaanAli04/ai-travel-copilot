/**
 * Time Picker Modal - Allow user to override current time
 */
import React, { useState } from 'react';
import { X, Clock } from 'lucide-react';

interface TimePickerModalProps {
  currentTime: string;
  onSelectTime: (time: string) => void;
  onClose: () => void;
}

export const TimePickerModal: React.FC<TimePickerModalProps> = ({
  currentTime,
  onSelectTime,
  onClose,
}) => {
  const timeOptions = [
    { value: 'morning', label: 'Morning (6 AM - 12 PM)', icon: '🌅' },
    { value: 'afternoon', label: 'Afternoon (12 PM - 5 PM)', icon: '☀️' },
    { value: 'evening', label: 'Evening (5 PM - 9 PM)', icon: '🌆' },
    { value: 'night', label: 'Night (9 PM - 6 AM)', icon: '🌙' },
  ];

  const [selectedTime, setSelectedTime] = useState(currentTime);

  const handleConfirm = () => {
    onSelectTime(selectedTime);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center backdrop-blur-sm"
    style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
    onClick={onClose}>
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4"
      onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">Select Time</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Time Options */}
        <div className="p-6 space-y-3">
          {timeOptions.map((option) => (
            <button
              key={option.value}
              onClick={() => setSelectedTime(option.value)}
              className={`w-full flex items-center gap-3 p-4 rounded-lg border-2 transition-all ${
                selectedTime === option.value
                  ? 'border-blue-600 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300 bg-white'
              }`}
            >
              <span className="text-2xl">{option.icon}</span>
              <div className="flex-1 text-left">
                <div className="font-medium text-gray-900">{option.label.split(' (')[0]}</div>
                <div className="text-sm text-gray-500">{option.label.match(/\(([^)]+)\)/)?.[1]}</div>
              </div>
              {selectedTime === option.value && (
                <div className="w-5 h-5 bg-blue-600 rounded-full flex items-center justify-center">
                  <div className="w-2 h-2 bg-white rounded-full"></div>
                </div>
              )}
            </button>
          ))}
        </div>

        {/* Footer */}
        <div className="flex gap-3 px-6 py-4 border-t bg-gray-50 rounded-b-xl">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
};
