import { type Trip } from '../services/api';
import { Calendar, Clock, DollarSign, MapPin, Sun, Cloud } from 'lucide-react';

interface ItineraryViewProps {
  trip: Trip;
}

const ItineraryView = ({ trip }: ItineraryViewProps) => {
  if (!trip.days || trip.days.length === 0) {
    return (
      <div className="glass-card rounded-3xl p-12 border-[rgba(148,163,184,0.2)] text-center">
        <div className="w-16 h-16 rounded-full bg-[#F97316]/10 flex items-center justify-center mx-auto mb-4">
          <Calendar className="w-8 h-8 text-[#F97316]" />
        </div>
        <h3 className="text-xl font-semibold text-white mb-2">No Itinerary Yet</h3>
        <p className="text-[#9CA3AF]">
          Click "Generate Itinerary" to create your AI-powered day-by-day trip plan
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center gap-3 mb-6">
        <Calendar className="w-6 h-6 text-[#38BDF8]" />
        <h2 className="text-2xl font-bold text-white">Your Itinerary</h2>
      </div>

      {trip.days.map((day, dayIndex) => (
        <div
          key={day.id}
          className="glass-card rounded-3xl p-6 border-[rgba(148,163,184,0.2)] animate-fade-in"
          style={{ animationDelay: `${dayIndex * 0.1}s` }}
        >
          {/* Day Header */}
          <div className="mb-6 pb-4 border-b border-[rgba(148,163,184,0.2)]">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className="px-3 py-1 rounded-full bg-[#38BDF8] text-white text-lg font-bold">
                  Day {day.day_number}
                </div>
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
                    {day.weather_condition && (
                      <div className="text-[#9CA3AF] text-xs">{day.weather_condition}</div>
                    )}
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

            {day.description && (
              <p className="text-[#E5E7EB] text-sm leading-relaxed">{day.description}</p>
            )}
          </div>

          {/* Activities Timeline */}
          <div className="space-y-4 ml-2 border-l-2 border-[#38BDF8]/30 pl-6">
            {day.activities && day.activities.length > 0 ? (
              day.activities.map((activity, index) => (
                <div key={activity.id} className="relative group">
                  {/* Timeline Dot */}
                  <div className="absolute -left-[1.69rem] top-2 w-3 h-3 rounded-full bg-[#38BDF8] border-4 border-[#111827] group-hover:scale-125 transition-transform" />

                  <div className="p-4 rounded-xl bg-[#1F2937]/50 border border-[rgba(148,163,184,0.2)] hover:bg-[#1F2937]/70 transition-all">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <h5 className="text-lg font-semibold text-white mb-2">
                          {index + 1}. {activity.title}
                        </h5>

                        {/* Time, Duration, Category */}
                        <div className="flex flex-wrap gap-3 text-sm text-[#9CA3AF]">
                          {activity.start_time && (
                            <div className="flex items-center gap-1">
                              <Clock className="w-4 h-4" />
                              {activity.start_time}
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
                    {activity.description && (
                      <p className="text-[#E5E7EB] text-sm mb-2 leading-relaxed">
                        {activity.description}
                      </p>
                    )}

                    {/* Location */}
                    {activity.location && (
                      <div className="flex items-center gap-1 text-sm text-[#9CA3AF] mt-2">
                        <MapPin className="w-4 h-4" />
                        {activity.location}
                      </div>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <p className="text-[#6B7280] italic">No activities planned for this day.</p>
            )}
          </div>

          {/* Day Total */}
          {day.activities && day.activities.length > 0 && (
            <div className="mt-6 pt-4 border-t border-[rgba(148,163,184,0.2)] flex items-center justify-between">
              <span className="text-[#9CA3AF]">Day Total</span>
              <span className="text-2xl font-bold text-white">
                ${day.activities.reduce((sum, act) => sum + (act.estimated_cost || 0), 0).toFixed(2)}
              </span>
            </div>
          )}
        </div>
      ))}

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
                .reduce(
                  (sum, day) =>
                    sum + (day.activities?.reduce((daySum, act) => daySum + (act.estimated_cost || 0), 0) || 0),
                  0
                )
                .toFixed(0)}
            </div>
            <div className="text-sm text-[#9CA3AF]">Total Cost</div>
          </div>

          {trip.budget && (
            <div className="text-center p-3 rounded-xl bg-[#1F2937]/50">
              <div
                className={`text-3xl font-bold mb-1 ${
                  trip.budget -
                    trip.days.reduce(
                      (sum, day) =>
                        sum + (day.activities?.reduce((daySum, act) => daySum + (act.estimated_cost || 0), 0) || 0),
                      0
                    ) >=
                  0
                    ? 'text-[#22C55E]'
                    : 'text-[#EF4444]'
                }`}
              >
                $
                {(
                  trip.budget -
                  trip.days.reduce(
                    (sum, day) =>
                      sum + (day.activities?.reduce((daySum, act) => daySum + (act.estimated_cost || 0), 0) || 0),
                    0
                  )
                ).toFixed(0)}
              </div>
              <div className="text-sm text-[#9CA3AF]">Remaining</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ItineraryView;
