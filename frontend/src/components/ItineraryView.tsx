import { useState } from 'react';
import { type Trip, activityApi, dayApi } from '../services/api';
import { Calendar, Clock, DollarSign, MapPin, HelpCircle, Trash2, ChevronUp, ChevronDown, Sparkles } from 'lucide-react';
import { ExplanationModal } from './ExplanationModal';
import { DeleteConfirmModal } from './DeleteConfirmModal';
import { ReplanDayModal } from './ReplanDayModal';
import type { ActivityExplanation } from '../services/api';
import { EditableActivityField } from './EditableActivityField';
import { ActivityPhotoSection } from './ActivityPhotoSection';

interface ItineraryViewProps {
  trip: Trip;
  onTripUpdate: () => void;
}

const ItineraryView = ({ trip, onTripUpdate }: ItineraryViewProps) => {
  const [explanationModal, setExplanationModal] = useState<{
    isOpen: boolean;
    activityId: number | null;
    activityTitle: string;
    explanation: ActivityExplanation | null;
    loading: boolean;
  }>({
    isOpen: false,
    activityId: null,
    activityTitle: '',
    explanation: null,
    loading: false,
  });

  const [deleteModal, setDeleteModal] = useState<{
    isOpen: boolean;
    activityId: number | null;
    activityTitle: string;
    loading: boolean;
  }>({
    isOpen: false,
    activityId: null,
    activityTitle: '',
    loading: false,
  });

  const [replanModal, setReplanModal] = useState<{
    isOpen: boolean;
    dayId: number | null;
    dayNumber: number;
    city: string;
    loading: boolean;
  }>({
    isOpen: false,
    dayId: null,
    dayNumber: 0,
    city: '',
    loading: false,
  });

  const [movingActivity, setMovingActivity] = useState<number | null>(null);

  // Explain activity
  const handleExplainActivity = async (activityId: number, activityTitle: string) => {
    setExplanationModal({
      isOpen: true,
      activityId,
      activityTitle,
      explanation: null,
      loading: true,
    });

    try {
      const explanation = await activityApi.explainActivity(activityId);
      setExplanationModal((prev) => ({
        ...prev,
        explanation,
        loading: false,
      }));
    } catch (error) {
      console.error('Failed to get explanation:', error);
      setExplanationModal((prev) => ({
        ...prev,
        loading: false,
      }));
    }
  };

  // Delete activity
  const handleDeleteActivity = async () => {
    if (!deleteModal.activityId) return;

    setDeleteModal((prev) => ({ ...prev, loading: true }));

    try {
      await activityApi.deleteActivity(deleteModal.activityId);
      setDeleteModal({
        isOpen: false,
        activityId: null,
        activityTitle: '',
        loading: false,
      });
      await onTripUpdate();
    } catch (error) {
      console.error('Failed to delete activity:', error);
      setDeleteModal((prev) => ({ ...prev, loading: false }));
    }
  };

  // Move activity up/down
    const handleMoveActivity = async (dayId: number, activityId: number, direction: 'up' | 'down') => {
    const day = trip.days.find((d) => d.id === dayId);
    if (!day || !day.activities) return;

    //SORT ACTIVITIES FIRST - This is the key fix!
    const sortedActivities = [...day.activities].sort((a, b) => a.order - b.order);
    
    console.log('Before move (sorted):', sortedActivities.map(a => ({ id: a.id, order: a.order, title: a.title })));

    const currentIndex = sortedActivities.findIndex((a) => a.id === activityId);
    if (currentIndex === -1) return;

    // Can't move up if first
    if (direction === 'up' && currentIndex === 0) return;
    // Can't move down if last
    if (direction === 'down' && currentIndex === sortedActivities.length - 1) return;

    setMovingActivity(activityId);

    try {
        // Create new order using SORTED activities
        const newOrder = [...sortedActivities];
        const targetIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1;
        [newOrder[currentIndex], newOrder[targetIndex]] = [newOrder[targetIndex], newOrder[currentIndex]];

        // Extract IDs
        const activityIds = newOrder.map((a) => a.id);
        console.log('New order being sent:', activityIds);

        await activityApi.reorderActivities(trip.id, dayId, activityIds);
        await onTripUpdate();
    } catch (error) {
        console.error('Failed to reorder activities:', error);
    } finally {
        setMovingActivity(null);
    }
    };

  // Replan day
  const handleReplanDay = async (preferences: string, keepExisting: boolean) => {
    if (!replanModal.dayId) return;

    setReplanModal((prev) => ({ ...prev, loading: true }));

    try {
      await dayApi.replanDay(trip.id, replanModal.dayId, preferences, keepExisting);
      setReplanModal({
        isOpen: false,
        dayId: null,
        dayNumber: 0,
        city: '',
        loading: false,
      });
      await onTripUpdate();
    } catch (error) {
      console.error('Failed to replan day:', error);
      setReplanModal((prev) => ({ ...prev, loading: false }));
    }
  };

  const handleUpdateActivity = async (
  activityId: number,
  updates: {
    title?: string;
    start_time?: string;
    end_time?: string;
  }
) => {
  try {
    const result = await activityApi.updateActivity(activityId, updates, true);
    
    // Show toast notification if other activities were adjusted
    if (result.adjusted_activities.length > 0) {
      console.log(`✅ Adjusted ${result.adjusted_activities.length} subsequent activities`);
      // You can add a toast notification here
    }
    
    await onTripUpdate();
  } catch (error) {
    console.error('Failed to update activity:', error);
    throw error;
  }
};

// Validation functions
const validateTime = (time: string): string | null => {
  const timeRegex = /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/;
  if (!timeRegex.test(time)) {
    return 'Invalid time format (use HH:MM)';
  }
  return null;
};

const validateTitle = (title: string): string | null => {
  if (!title.trim()) {
    return 'Title cannot be empty';
  }
  if (title.length > 200) {
    return 'Title too long (max 200 characters)';
  }
  return null;
};

  if (!trip.days || trip.days.length === 0) {
    return (
      <div className="glass-card rounded-3xl p-12 border-[rgba(148,163,184,0.2)] text-center">
        <div className="w-16 h-16 rounded-full bg-[#F97316]/10 flex items-center justify-center mx-auto mb-4">
          <Calendar className="w-8 h-8 text-[#F97316]" />
        </div>
        <h3 className="text-xl font-semibold text-white mb-2">No Itinerary Yet</h3>
        <p className="text-[#9CA3AF]">Click "Generate Itinerary" to create your AI-powered day-by-day trip plan</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center gap-3 mb-6">
        <Calendar className="w-6 h-6 text-[#38BDF8]" />
        <h2 className="text-2xl font-bold text-white">Your Itinerary</h2>
      </div>

      {trip.days.map((day, dayIndex) => {
        // ✅ Sort activities before rendering
        const sortedActivities = day.activities ? [...day.activities].sort((a, b) => a.order - b.order) : [];
        
        return (
            <div
            key={day.id}
            className="glass-card rounded-3xl p-6 border-[rgba(148,163,184,0.2)] animate-fade-in"
            style={{ animationDelay: `${dayIndex * 0.1}s` }}
            >
            {/* Day Header */}
            <div className="mb-6 pb-4 border-b border-[rgba(148,163,184,0.2)]">
                <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                    <div className="px-3 py-1 rounded-full bg-[#38BDF8] text-white text-lg font-bold">Day {day.day_number}</div>
                    <div>
                    <h3 className="text-xl font-bold text-white">
                        {new Date(day.date).toLocaleDateString('en-US', {
                        weekday: 'long',
                        month: 'long',
                        day: 'numeric',
                        })}
                    </h3>
                    {day.city && (
                        <p className="text-sm text-[#9CA3AF] mt-1">
                        <MapPin className="w-4 h-4 inline mr-1" />
                        {day.city}
                        </p>
                    )}
                    </div>
                </div>

                {/* Weather Badge */}
                {day.weather_icon && (
                    <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[#38BDF8]/10 border border-[#38BDF8]/30">
                    <span className="text-2xl">{day.weather_icon}</span>
                    <div className="text-sm">
                        <div className="text-white font-semibold">
                        {day.weather_temp_high}°C / {day.weather_temp_low}°C
                        </div>
                        {day.weather_condition && <div className="text-[#9CA3AF] text-xs">{day.weather_condition}</div>}
                    </div>
                    </div>
                )}
                </div>

                {day.theme && (
                <div className="flex items-center gap-2 mb-2">
                    <span className="text-2xl">🎯</span>
                    <h4 className="text-lg font-semibold text-[#38BDF8]">{day.theme}</h4>
                </div>
                )}

                {day.description && <p className="text-[#E5E7EB] text-sm leading-relaxed">{day.description}</p>}

                {/* Re-plan Day Button */}
                <div className="mt-4">
                <button
                    onClick={() =>
                    setReplanModal({
                        isOpen: true,
                        dayId: day.id,
                        dayNumber: day.day_number,
                        city: day.city,
                        loading: false,
                    })
                    }
                    className="px-4 py-2 rounded-lg bg-[#8B5CF6]/10 border border-[#8B5CF6]/30 text-[#8B5CF6] hover:bg-[#8B5CF6]/20 transition-all text-sm font-medium flex items-center gap-2 cursor-pointer"
                >
                    <Sparkles className="w-4 h-4" />
                    Re-plan This Day
                </button>
                </div>
            </div>

            {/* Activities Timeline */}
            <div className="space-y-4 ml-2 border-l-2 border-[#38BDF8]/30 pl-6">
                {sortedActivities.length > 0 ? (
                sortedActivities.map((activity, index) => (
                    <div key={activity.id} className="relative group">
                    {/* Timeline Dot */}
                    <div className="absolute -left-[1.69rem] top-2 w-3 h-3 rounded-full bg-[#38BDF8] border-4 border-[#111827] group-hover:scale-125 transition-transform" />

                    <div className="p-4 rounded-xl bg-[#1F2937]/50 border border-[rgba(148,163,184,0.2)] hover:bg-[#1F2937]/70 transition-all">
                        <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                            {/* Editable Title */}
                            <div className="mb-2">
                            <span className="text-white font-semibold mr-2">{activity.order}.</span>
                            <EditableActivityField
                                value={activity.title}
                                type="text"
                                onSave={(newTitle) => handleUpdateActivity(activity.id, { title: newTitle })}
                                placeholder="Activity title"
                                className="inline-flex text-lg font-semibold text-white"
                                validate={validateTitle}
                            />
                            </div>

                            {/* Editable Times */}
                            <div className="flex flex-wrap gap-3 text-sm text-[#9CA3AF]">
                            {(activity.start_time || activity.end_time) && (
                                <div className="flex items-center gap-2">
                                <Clock className="w-4 h-4" />
                                
                                {activity.start_time && (
                                    <EditableActivityField
                                    value={activity.start_time}
                                    type="time"
                                    onSave={(newTime) => handleUpdateActivity(activity.id, { start_time: newTime })}
                                    className="text-sm"
                                    validate={validateTime}
                                    />
                                )}
                                
                                {activity.start_time && activity.end_time && (
                                    <span className="text-[#6B7280]">-</span>
                                )}
                                
                                {activity.end_time && (
                                    <EditableActivityField
                                    value={activity.end_time}
                                    type="time"
                                    onSave={(newTime) => handleUpdateActivity(activity.id, { end_time: newTime })}
                                    className="text-sm"
                                    validate={validateTime}
                                    />
                                )}
                                </div>
                            )}
                            
                            {activity.duration_minutes && (
                                <div className="flex items-center gap-1">
                                ⏱️ {activity.duration_minutes} min
                                </div>
                            )}
                            
                            {activity.category && (
                                <div className="px-2 py-1 rounded-full bg-[#38BDF8]/10 text-[#38BDF8] text-xs font-medium">
                                {activity.category}
                                </div>
                            )}
                            </div>
                        </div>

                        {/* Cost Badge */}
                        {activity.estimated_cost !== undefined && activity.estimated_cost > 0 && (
                            <div className="px-3 py-1 rounded-lg bg-[#22C55E]/10 border border-[#22C55E]/30 text-[#22C55E] font-bold whitespace-nowrap ml-3">
                            ${activity.estimated_cost}
                            </div>
                        )}
                        </div>
                        

                        {/* Description */}
                        {activity.description && <p className="text-[#E5E7EB] text-sm mb-3 leading-relaxed">{activity.description}</p>}

                        {/* Location */}
                        {activity.location && (
                        <div className="flex items-center gap-1 text-sm text-[#9CA3AF] mb-3">
                            <MapPin className="w-4 h-4" />
                            {activity.location}
                        </div>
                        )}

                        {/* Action Buttons */}
                        <div className="flex items-center gap-2 pt-3 border-t border-[rgba(148,163,184,0.1)]">
                        <button
                            onClick={() => handleExplainActivity(activity.id, activity.title)}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#60A5FA]/10 border border-[#60A5FA]/30 text-[#60A5FA] hover:bg-[#60A5FA]/20 transition-all text-sm font-medium cursor-pointer"
                        >
                            <HelpCircle className="w-4 h-4" />
                            Why this?
                        </button>
                        <ActivityPhotoSection    
                          activityId={activity.id}
                          activityTitle={activity.title}
                          category={activity.category}
                        />

                        <button
                            onClick={() =>
                            setDeleteModal({
                                isOpen: true,
                                activityId: activity.id,
                                activityTitle: activity.title,
                                loading: false,
                            })
                            }
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#EF4444]/10 border border-[#EF4444]/30 text-[#EF4444] hover:bg-[#EF4444]/20 transition-all text-sm font-medium cursor-pointer"
                        >
                            <Trash2 className="w-4 h-4" />
                            Delete
                        </button>

                        <div className="flex items-center gap-1 ml-auto">
                            <button
                            onClick={() => handleMoveActivity(day.id, activity.id, 'up')}
                            disabled={index === 0 || movingActivity === activity.id}
                            className="p-1.5 rounded-lg bg-white/5 border border-[rgba(148,163,184,0.2)] hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                            title="Move up"
                            >
                            <ChevronUp className="w-4 h-4 text-gray-400" />
                            </button>
                            <button
                            onClick={() => handleMoveActivity(day.id, activity.id, 'down')}
                            disabled={index === sortedActivities.length - 1 || movingActivity === activity.id}
                            className="p-1.5 rounded-lg bg-white/5 border border-[rgba(148,163,184,0.2)] hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                            title="Move down"
                            >
                            <ChevronDown className="w-4 h-4 text-gray-400" />
                            </button>
                        </div>
                        </div>
                    </div>
                    </div>
                ))
                ) : (
                <p className="text-[#6B7280] italic">No activities planned for this day.</p>
                )}
            </div>

            {/* Day Total */}
            {sortedActivities.length > 0 && (
                <div className="mt-6 pt-4 border-t border-[rgba(148,163,184,0.2)] flex items-center justify-between">
                <span className="text-[#9CA3AF]">Day Total</span>
                <span className="text-2xl font-bold text-white">
                    ${sortedActivities.reduce((sum, act) => sum + (act.estimated_cost || 0), 0).toFixed(2)}
                </span>
                </div>
            )}
            </div>
        );
        })}

      {/* Trip Summary Card */}
      <div className="glass-card rounded-3xl p-6 border-[rgba(148,163,184,0.2)] bg-gradient-to-br from-[#22C55E]/10 to-[#38BDF8]/10">
        <div className="flex items-center gap-2 mb-4">
          <DollarSign className="w-6 h-6 text-[#22C55E]" />
          <h3 className="text-xl font-bold text-white">Trip Summary</h3>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="text-center p-3 rounded-xl bg-[#1F2937]/50">
            <div className="text-3xl font-bold text-[#38BDF8] mb-1">{trip.days.length}</div>
            <div className="text-sm text-[#9CA3AF]">Days</div>
          </div>

          <div className="text-center p-3 rounded-xl bg-[#1F2937]/50">
            <div className="text-3xl font-bold text-[#F97316] mb-1">
              {trip.days.reduce((sum, day) => sum + (day.activities?.length || 0), 0)}
            </div>
            <div className="text-sm text-[#9CA3AF]">Activities</div>
          </div>

          <div className="text-center p-3 rounded-xl bg-[#1F2937]/50">
            <div className="text-3xl font-bold text-[#22C55E] mb-1">
              $
              {trip.days
                .reduce((sum, day) => sum + (day.activities?.reduce((daySum, act) => daySum + (act.estimated_cost || 0), 0) || 0), 0)
                .toFixed(0)}
            </div>
            <div className="text-sm text-[#9CA3AF]">Total Cost</div>
          </div>

          {trip.budget && (
                <div className="text-center p-3 rounded-xl bg-[#1F2937]/50">
                    {(() => {
                    const remaining = trip.budget - trip.days.reduce(
                        (sum, day) =>
                        sum + (day.activities?.reduce((daySum, act) => daySum + (act.estimated_cost || 0), 0) || 0),
                        0
                    );
                    const isUnderBudget = remaining >= 0;
                    
                    return (
                        <>
                        <div className={`text-3xl font-bold mb-1 ${isUnderBudget ? 'text-[#22C55E]' : 'text-[#EF4444]'}`}>
                            ${remaining.toFixed(0)}
                        </div>
                        <div className="text-sm text-[#9CA3AF] mb-1">Remaining</div>
                        <div className={`text-xs px-2 py-0.5 rounded-full inline-block ${
                            isUnderBudget 
                            ? 'bg-[#22C55E]/10 text-[#22C55E]' 
                            : 'bg-[#EF4444]/10 text-[#EF4444]'
                        }`}>
                            {isUnderBudget ? '✓ Under Budget' : '⚠ Over Budget'}
                        </div>
                        </>
                    );
                    })()}
                </div>
            )}
        </div>
      </div>

      {/* Modals */}
      <ExplanationModal
        isOpen={explanationModal.isOpen}
        onClose={() =>
          setExplanationModal({
            isOpen: false,
            activityId: null,
            activityTitle: '',
            explanation: null,
            loading: false,
          })
        }
        explanation={explanationModal.explanation}
        activityTitle={explanationModal.activityTitle}
        loading={explanationModal.loading}
      />

      <DeleteConfirmModal
        isOpen={deleteModal.isOpen}
        onClose={() =>
          setDeleteModal({
            isOpen: false,
            activityId: null,
            activityTitle: '',
            loading: false,
          })
        }
        onConfirm={handleDeleteActivity}
        title="Delete Activity"
        message={`Are you sure you want to delete "${deleteModal.activityTitle}"? This action cannot be undone.`}
        loading={deleteModal.loading}
      />

      <ReplanDayModal
        isOpen={replanModal.isOpen}
        onClose={() =>
          setReplanModal({
            isOpen: false,
            dayId: null,
            dayNumber: 0,
            city: '',
            loading: false,
          })
        }
        onReplan={handleReplanDay}
        dayNumber={replanModal.dayNumber}
        city={replanModal.city}
        loading={replanModal.loading}
      />
    </div>
  );
};

export default ItineraryView;
