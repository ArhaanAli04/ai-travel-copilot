import React, { useState } from 'react';
import { Images } from 'lucide-react';
import { ActivityPhotoModal } from './ActivityPhotoModal';

interface ActivityPhotoSectionProps {
  activityId: number;
  activityTitle: string;
  category?: string;
}

export const ActivityPhotoSection: React.FC<ActivityPhotoSectionProps> = ({
  activityId,
  activityTitle,
  category,
}) => {
  const [showModal, setShowModal] = useState(false);

  return (
    <>
      <button
        onClick={() => setShowModal(true)}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#F59E0B]/10 border border-[#F59E0B]/30 text-[#F59E0B] hover:bg-[#F59E0B]/20 transition-all text-sm font-medium"
      >
        <Images className="w-4 h-4" />
        View Photos
      </button>

      {showModal && (
        <ActivityPhotoModal
          activityId={activityId}
          activityTitle={activityTitle}
          category={category}
          onClose={() => setShowModal(false)}
        />
      )}
    </>
  );
};
