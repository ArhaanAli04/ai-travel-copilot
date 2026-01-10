import { type Trip } from '../services/api';

interface ItineraryViewProps {
  trip: Trip;
}

const ItineraryView = ({ trip }: ItineraryViewProps) => {
  if (!trip.days || trip.days.length === 0) {
    return (
      <div style={{ 
        padding: '2rem', 
        background: '#fff3cd', 
        borderRadius: '12px',
        textAlign: 'center' 
      }}>
        <p style={{ fontSize: '1.1rem', color: '#856404' }}>
          ℹ️ No itinerary generated yet. Click "Generate Itinerary" to create your trip plan.
        </p>
      </div>
    );
  }

  return (
    <div style={{ marginTop: '2rem' }}>
      <h2 style={{ marginBottom: '1.5rem', color: '#333' }}>
        📅 Your Itinerary
      </h2>

      {trip.days.map((day) => (
        <div 
          key={day.id}
          style={{
            marginBottom: '2rem',
            padding: '1.5rem',
            background: '#fff',
            borderRadius: '12px',
            border: '2px solid #e0e0e0',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}
        >
          {/* Day Header */}
          <div style={{ 
            marginBottom: '1rem',
            paddingBottom: '1rem',
            borderBottom: '2px solid #f0f0f0'
          }}>
            <h3 style={{ 
              fontSize: '1.5rem', 
              color: '#2196F3',
              marginBottom: '0.5rem'
            }}>
              Day {day.day_number} - {new Date(day.date).toLocaleDateString('en-US', { 
                weekday: 'long', 
                month: 'short', 
                day: 'numeric' 
              })}
            </h3>
            
            {day.theme && (
              <p style={{ 
                fontSize: '1.1rem', 
                fontWeight: 'bold',
                color: '#666',
                marginBottom: '0.5rem'
              }}>
                🎯 {day.theme}
              </p>
            )}

            {day.description && (
              <p style={{ 
                color: '#777',
                marginBottom: '0.5rem'
              }}>
                {day.description}
              </p>
            )}

            {/* Weather Info */}
            {day.weather_icon && (
              <div style={{ 
                display: 'flex', 
                gap: '1rem',
                alignItems: 'center',
                marginTop: '0.5rem',
                padding: '0.5rem',
                background: '#f8f9fa',
                borderRadius: '8px'
              }}>
                <span style={{ fontSize: '1.5rem' }}>{day.weather_icon}</span>
                <span style={{ color: '#666' }}>
                  {day.weather_temp_high}°C / {day.weather_temp_low}°C
                  {day.weather_condition && ` - ${day.weather_condition}`}
                </span>
              </div>
            )}
          </div>

          {/* Activities List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {day.activities && day.activities.length > 0 ? (
              day.activities.map((activity, index) => (
                <div 
                  key={activity.id}
                  style={{
                    padding: '1rem',
                    background: '#f8f9fa',
                    borderRadius: '8px',
                    borderLeft: '4px solid #4CAF50'
                  }}
                >
                  {/* Activity Header */}
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    marginBottom: '0.5rem'
                  }}>
                    <div style={{ flex: 1 }}>
                      <h4 style={{ 
                        fontSize: '1.1rem', 
                        color: '#333',
                        marginBottom: '0.25rem'
                      }}>
                        {index + 1}. {activity.title}
                      </h4>
                      
                      {/* Time and Duration */}
                      <div style={{ 
                        display: 'flex', 
                        gap: '1rem',
                        fontSize: '0.9rem',
                        color: '#666',
                        marginBottom: '0.5rem'
                      }}>
                        {activity.start_time && (
                          <span>🕐 {activity.start_time}</span>
                        )}
                        {activity.duration_minutes && (
                          <span>⏱️ {activity.duration_minutes} min</span>
                        )}
                        {activity.category && (
                          <span style={{ 
                            padding: '0.25rem 0.5rem',
                            background: '#e3f2fd',
                            borderRadius: '4px',
                            fontSize: '0.85rem'
                          }}>
                            {activity.category}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Cost */}
                    {activity.estimated_cost !== undefined && activity.estimated_cost > 0 && (
                      <div style={{ 
                        fontSize: '1.1rem',
                        fontWeight: 'bold',
                        color: '#4CAF50',
                        textAlign: 'right'
                      }}>
                        ${activity.estimated_cost}
                      </div>
                    )}
                  </div>

                  {/* Description */}
                  {activity.description && (
                    <p style={{ 
                      color: '#555',
                      marginBottom: '0.5rem',
                      fontSize: '0.95rem'
                    }}>
                      {activity.description}
                    </p>
                  )}

                  {/* Location */}
                  {activity.location && (
                    <p style={{ 
                      color: '#888',
                      fontSize: '0.9rem',
                      marginTop: '0.5rem'
                    }}>
                      📍 {activity.location}
                    </p>
                  )}
                </div>
              ))
            ) : (
              <p style={{ color: '#999', fontStyle: 'italic' }}>
                No activities planned for this day.
              </p>
            )}
          </div>

          {/* Day Total Cost */}
          {day.activities && day.activities.length > 0 && (
            <div style={{ 
              marginTop: '1rem',
              paddingTop: '1rem',
              borderTop: '2px solid #f0f0f0',
              textAlign: 'right'
            }}>
              <span style={{ fontSize: '1.1rem', color: '#666' }}>
                Day Total: 
              </span>
              <span style={{ 
                fontSize: '1.3rem', 
                fontWeight: 'bold',
                color: '#4CAF50',
                marginLeft: '0.5rem'
              }}>
                ${day.activities.reduce((sum, act) => sum + (act.estimated_cost || 0), 0).toFixed(2)}
              </span>
            </div>
          )}
        </div>
      ))}

      {/* Trip Summary */}
      <div style={{
        marginTop: '2rem',
        padding: '1.5rem',
        background: '#e8f5e9',
        borderRadius: '12px',
        border: '2px solid #4CAF50'
      }}>
        <h3 style={{ color: '#4CAF50', marginBottom: '1rem' }}>
          💰 Trip Summary
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div>
            <p style={{ color: '#666', marginBottom: '0.25rem' }}>Total Days:</p>
            <p style={{ fontSize: '1.3rem', fontWeight: 'bold', color: '#333' }}>
              {trip.days.length}
            </p>
          </div>
          <div>
            <p style={{ color: '#666', marginBottom: '0.25rem' }}>Total Activities:</p>
            <p style={{ fontSize: '1.3rem', fontWeight: 'bold', color: '#333' }}>
              {trip.days.reduce((sum, day) => sum + (day.activities?.length || 0), 0)}
            </p>
          </div>
          <div>
            <p style={{ color: '#666', marginBottom: '0.25rem' }}>Estimated Cost:</p>
            <p style={{ fontSize: '1.3rem', fontWeight: 'bold', color: '#4CAF50' }}>
              ${trip.days.reduce((sum, day) => 
                sum + (day.activities?.reduce((daySum, act) => 
                  daySum + (act.estimated_cost || 0), 0) || 0), 0
              ).toFixed(2)}
            </p>
          </div>
          {trip.budget && (
            <div>
              <p style={{ color: '#666', marginBottom: '0.25rem' }}>Budget Remaining:</p>
              <p style={{ 
                fontSize: '1.3rem', 
                fontWeight: 'bold', 
                color: trip.budget - trip.days.reduce((sum, day) => 
                  sum + (day.activities?.reduce((daySum, act) => 
                    daySum + (act.estimated_cost || 0), 0) || 0), 0
                ) >= 0 ? '#4CAF50' : '#f44'
              }}>
                ${(trip.budget - trip.days.reduce((sum, day) => 
                  sum + (day.activities?.reduce((daySum, act) => 
                    daySum + (act.estimated_cost || 0), 0) || 0), 0
                )).toFixed(2)}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ItineraryView;
