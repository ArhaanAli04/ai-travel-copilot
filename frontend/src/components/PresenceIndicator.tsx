interface PresenceIndicatorProps {
  viewers: string[];        // display names currently viewing
  currentUserName: string;  // to exclude self
}

export function PresenceIndicator({ viewers, currentUserName }: PresenceIndicatorProps) {
  // Filter out current user
  const others = viewers.filter(v => v !== currentUserName);
  if (others.length === 0) return null;

  const MAX_SHOWN = 3;
  const shown = others.slice(0, MAX_SHOWN);
  const overflow = others.length - MAX_SHOWN;

  return (
    <div className="flex items-center gap-2">
      <div className="flex -space-x-2">
        {shown.map((name, i) => (
          <div
            key={i}
            title={`${name} is viewing`}
            className="w-7 h-7 rounded-full bg-gradient-to-br from-[#38BDF8]/40 to-[#F97316]/40
              border-2 border-[#0a0e14] flex items-center justify-center
              text-[10px] font-bold text-white uppercase"
          >
            {name[0]}
          </div>
        ))}
        {overflow > 0 && (
          <div className="w-7 h-7 rounded-full bg-[#374151] border-2 border-[#0a0e14]
            flex items-center justify-center text-[10px] font-bold text-white">
            +{overflow}
          </div>
        )}
      </div>
      <span className="text-xs text-[#6B7280]">
        {others.length === 1
          ? `${others[0]} is viewing`
          : `${others.length} others viewing`}
      </span>
      {/* Live pulse dot */}
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#22C55E] opacity-75" />
        <span className="relative inline-flex rounded-full h-2 w-2 bg-[#22C55E]" />
      </span>
    </div>
  );
}
