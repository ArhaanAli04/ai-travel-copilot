import React, { useState, useEffect } from 'react';
import { Card } from './shared/Card';
import { disruptionApi } from '../services/api';
import type { DisruptionCase } from '../types/disruption';

interface WeatherAlertCardProps {
  disruptionCase: DisruptionCase;
}

const severityConfig = {
  low:    { color: 'text-green-400',  bg: 'bg-green-500/10',  border: 'border-green-500/30',  icon: '✅', label: 'Clear' },
  medium: { color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', icon: '⚠️', label: 'Caution' },
  high:   { color: 'text-red-400',    bg: 'bg-red-500/10',    border: 'border-red-500/30',    icon: '🚨', label: 'Severe' },
};

export const WeatherAlertCard: React.FC<WeatherAlertCardProps> = ({ disruptionCase }) => {
  const [weather, setWeather] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchWeather();
  }, [disruptionCase.id]);

  const fetchWeather = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await disruptionApi.getWeather(disruptionCase.id);
      setWeather(data.weather);
    } catch (err: any) {
      setError('Failed to load weather');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card className="space-y-4">
        <div className="flex items-center gap-2">
          <span>🌤️</span>
          <h3 className="text-white font-semibold">Weather</h3>
        </div>
        <div className="flex items-center justify-center py-4">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500" />
        </div>
      </Card>
    );
  }

  if (!weather || error) {
    return (
      <Card className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span>🌤️</span>
            <h3 className="text-white font-semibold">Weather</h3>
          </div>
          <button onClick={fetchWeather} className="text-xs text-gray-400 hover:text-white transition-colors">
            🔄 Retry
          </button>
        </div>
        <div className="text-gray-400 text-sm text-center py-4">
          {error || 'No weather data available'}
        </div>
      </Card>
    );
  }

  const severity = weather.severity || 'low';
  const config = severityConfig[severity as keyof typeof severityConfig] || severityConfig.low;

  return (
    <Card className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-white font-semibold flex items-center gap-2">
          <span>{weather.icon}</span> Weather
        </h3>
        <div className="flex items-center gap-2">
          <div className={`px-2 py-1 rounded-lg ${config.bg} border ${config.border}`}>
            <span className="text-xs font-medium">{config.icon} {config.label}</span>
          </div>
          <button onClick={fetchWeather} className="text-gray-400 hover:text-white transition-colors text-xs">
            🔄
          </button>
        </div>
      </div>

      {/* Condition */}
      <div className={`p-3 rounded-lg ${config.bg} border ${config.border} flex items-center justify-between`}>
        <span className={`text-sm font-semibold ${config.color}`}>{weather.condition}</span>
        <span className="text-2xl">{weather.icon}</span>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-2">
        {/* Temperature */}
        <div className="p-2.5 rounded-lg bg-[rgba(15,23,42,0.5)] border border-[rgba(148,163,184,0.1)]">
          <p className="text-xs text-gray-500 mb-1">🌡️ Temperature</p>
          <p className="text-white text-sm font-semibold">
            {Math.round(weather.temp_min)}° – {Math.round(weather.temp_max)}°C
          </p>
        </div>

        {/* Precipitation */}
        <div className="p-2.5 rounded-lg bg-[rgba(15,23,42,0.5)] border border-[rgba(148,163,184,0.1)]">
          <p className="text-xs text-gray-500 mb-1">🌧️ Rain Chance</p>
          <p className={`text-sm font-semibold ${
            weather.precipitation_probability > 70 ? 'text-blue-400'
            : weather.precipitation_probability > 30 ? 'text-yellow-400'
            : 'text-green-400'
          }`}>
            {Math.round(weather.precipitation_probability)}%
          </p>
        </div>

        {/* Wind */}
        {weather.wind_speed_max != null && (
          <div className="p-2.5 rounded-lg bg-[rgba(15,23,42,0.5)] border border-[rgba(148,163,184,0.1)]">
            <p className="text-xs text-gray-500 mb-1">💨 Max Wind</p>
            <p className={`text-sm font-semibold ${
              weather.wind_speed_max > 50 ? 'text-red-400'
              : weather.wind_speed_max > 30 ? 'text-yellow-400'
              : 'text-white'
            }`}>
              {Math.round(weather.wind_speed_max)} km/h
            </p>
          </div>
        )}

        {/* UV Index */}
        {weather.uv_index_max != null && (
          <div className="p-2.5 rounded-lg bg-[rgba(15,23,42,0.5)] border border-[rgba(148,163,184,0.1)]">
            <p className="text-xs text-gray-500 mb-1">☀️ UV Index</p>
            <p className={`text-sm font-semibold ${
              weather.uv_index_max >= 8 ? 'text-red-400'
              : weather.uv_index_max >= 6 ? 'text-orange-400'
              : weather.uv_index_max >= 3 ? 'text-yellow-400'
              : 'text-green-400'
            }`}>
              {Math.round(weather.uv_index_max)} {weather.uv_index_max >= 8 ? '(Very High)' : weather.uv_index_max >= 6 ? '(High)' : weather.uv_index_max >= 3 ? '(Moderate)' : '(Low)'}
            </p>
          </div>
        )}

        {/* Visibility */}
        {weather.visibility_mean != null && (
          <div className="p-2.5 rounded-lg bg-[rgba(15,23,42,0.5)] border border-[rgba(148,163,184,0.1)]">
            <p className="text-xs text-gray-500 mb-1">👁️ Visibility</p>
            <p className={`text-sm font-semibold ${
              weather.visibility_mean < 1000 ? 'text-red-400'
              : weather.visibility_mean < 5000 ? 'text-yellow-400'
              : 'text-white'
            }`}>
              {weather.visibility_mean >= 1000
                ? `${(weather.visibility_mean / 1000).toFixed(1)} km`
                : `${Math.round(weather.visibility_mean)} m`}
            </p>
          </div>
        )}

        {/* Sunrise / Sunset */}
        {weather.sunrise && weather.sunset && (
          <div className="p-2.5 rounded-lg bg-[rgba(15,23,42,0.5)] border border-[rgba(148,163,184,0.1)]">
            <p className="text-xs text-gray-500 mb-1">🌅 Sun</p>
            <p className="text-white text-xs">
              ↑ {new Date(weather.sunrise).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })}
              {' · '}
              ↓ {new Date(weather.sunset).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })}
            </p>
          </div>
        )}
      </div>

      {/* Severe warning */}
      {severity === 'high' && (
        <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
          <div className="flex items-start gap-2 text-sm text-red-300">
            <span className="flex-shrink-0">⚠️</span>
            <div>
              <div className="font-semibold mb-1">Severe Weather Alert</div>
              <div className="text-red-400/80 text-xs">Flight delays or cancellations possible. Check with your airline.</div>
            </div>
          </div>
        </div>
      )}

      {/* Location + timestamp */}
      <div className="pt-3 border-t border-[rgba(148,163,184,0.2)] flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center gap-1">
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
          </svg>
          <span>{weather.city || weather.airport_code}</span>
        </div>
        {weather.fetched_at && (
          <span>Updated {new Date(weather.fetched_at).toLocaleTimeString()}</span>
        )}
      </div>
    </Card>
  );
};

export default WeatherAlertCard;
