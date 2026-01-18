import React from 'react';
import { Card } from './shared/Card';
import type { DisruptionCase } from '../types/disruption';

interface WeatherAlertCardProps {
  disruptionCase: DisruptionCase;
}

const severityConfig = {
  low: {
    color: 'text-green-400',
    bg: 'bg-green-500/10',
    border: 'border-green-500/30',
    icon: '✅',
    label: 'Clear',
  },
  medium: {
    color: 'text-yellow-400',
    bg: 'bg-yellow-500/10',
    border: 'border-yellow-500/30',
    icon: '⚠️',
    label: 'Caution',
  },
  high: {
    color: 'text-red-400',
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
    icon: '🚨',
    label: 'Severe',
  },
};

const weatherIcons: Record<string, string> = {
  Clear: '☀️',
  Sunny: '☀️',
  Cloudy: '☁️',
  'Partly Cloudy': '⛅',
  Overcast: '☁️',
  Rain: '🌧️',
  'Light Rain': '🌦️',
  'Heavy Rain': '⛈️',
  Storm: '⛈️',
  Thunderstorm: '⛈️',
  Snow: '❄️',
  Fog: '🌫️',
  Mist: '🌫️',
  Windy: '💨',
};

export const WeatherAlertCard: React.FC<WeatherAlertCardProps> = ({ disruptionCase }) => {
  const weather = disruptionCase.meta_data?.weather;
  
  if (!weather) {
    return (
      <Card className="space-y-4">
        <div className="flex items-center gap-2">
          <span>🌤️</span>
          <h3 className="text-white font-semibold">Weather</h3>
        </div>
        <div className="text-gray-400 text-sm text-center py-4">
          No weather data available
        </div>
      </Card>
    );
  }

  const severity = weather.severity || 'low';
  const config = severityConfig[severity as keyof typeof severityConfig] || severityConfig.low;
  const weatherIcon = weatherIcons[weather.condition] || '🌤️';

  return (
    <Card className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-white font-semibold flex items-center gap-2">
          <span>🌤️</span>
          Weather Alert
        </h3>
        <div className={`px-2 py-1 rounded-lg ${config.bg} border ${config.border}`}>
          <span className="text-xs font-medium">{config.icon}</span>
        </div>
      </div>

      {/* Severity Badge */}
      <div className={`p-3 rounded-lg ${config.bg} border ${config.border}`}>
        <div className="flex items-center justify-between">
          <span className={`text-sm font-semibold ${config.color}`}>
            {config.label}
          </span>
          <span className="text-2xl">{weatherIcon}</span>
        </div>
      </div>

      {/* Condition */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-gray-400 text-sm">Condition</span>
          <span className="text-white font-medium">{weather.condition}</span>
        </div>

        {/* Temperature */}
        {weather.temperature !== undefined && (
          <div className="flex items-center justify-between">
            <span className="text-gray-400 text-sm">Temperature</span>
            <span className="text-white font-medium">
              {Math.round(weather.temperature)}°C
              {weather.temperature_apparent !== undefined && 
               weather.temperature_apparent !== weather.temperature && (
                <span className="text-gray-500 text-xs ml-1">
                  (feels {Math.round(weather.temperature_apparent)}°C)
                </span>
              )}
            </span>
          </div>
        )}

        {/* Precipitation */}
        {weather.precipitation_probability !== undefined && (
          <div className="flex items-center justify-between">
            <span className="text-gray-400 text-sm">Precipitation</span>
            <span className={`font-medium ${
              weather.precipitation_probability > 70 
                ? 'text-blue-400' 
                : weather.precipitation_probability > 30 
                ? 'text-yellow-400' 
                : 'text-green-400'
            }`}>
              {weather.precipitation_probability}%
            </span>
          </div>
        )}

        {/* Wind Speed */}
        {weather.wind_speed !== undefined && (
          <div className="flex items-center justify-between">
            <span className="text-gray-400 text-sm">Wind Speed</span>
            <span className={`font-medium ${
              weather.wind_speed > 50 
                ? 'text-red-400' 
                : weather.wind_speed > 30 
                ? 'text-yellow-400' 
                : 'text-white'
            }`}>
              {Math.round(weather.wind_speed)} km/h
            </span>
          </div>
        )}

        {/* Visibility */}
        {weather.visibility !== undefined && (
          <div className="flex items-center justify-between">
            <span className="text-gray-400 text-sm">Visibility</span>
            <span className={`font-medium ${
              weather.visibility < 1 
                ? 'text-red-400' 
                : weather.visibility < 5 
                ? 'text-yellow-400' 
                : 'text-white'
            }`}>
              {weather.visibility.toFixed(1)} km
            </span>
          </div>
        )}

        {/* Humidity */}
        {weather.humidity !== undefined && (
          <div className="flex items-center justify-between">
            <span className="text-gray-400 text-sm">Humidity</span>
            <span className="text-white font-medium">
              {weather.humidity}%
            </span>
          </div>
        )}
      </div>

      {/* Location */}
      <div className="pt-3 border-t border-[rgba(148,163,184,0.2)]">
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
          </svg>
          <span>{weather.airport_code || disruptionCase.origin}</span>
        </div>
      </div>

      {/* Weather Warnings */}
      {severity === 'high' && (
        <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
          <div className="flex items-start gap-2">
            <span className="text-red-400 text-lg flex-shrink-0">⚠️</span>
            <div className="text-sm text-red-300">
              <div className="font-semibold mb-1">Severe Weather Alert</div>
              <div className="text-red-400/80">
                Flight delays or cancellations are possible. Check with your airline for updates.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Last Updated */}
      {weather.fetched_at && (
        <div className="text-xs text-gray-500 text-center pt-2 border-t border-[rgba(148,163,184,0.2)]">
          Updated {new Date(weather.fetched_at).toLocaleTimeString()}
        </div>
      )}
    </Card>
  );
};

export default WeatherAlertCard;
