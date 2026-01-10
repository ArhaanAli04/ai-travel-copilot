export function Hero() {
  return (
    <section className="relative pt-16 pb-12">
      <div className="absolute inset-0 bg-gradient-to-b from-[#3B82F6]/10 via-[#8B5CF6]/5 to-transparent pointer-events-none" />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
        <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4 animate-fade-in">
          ✈️ Trip Planner
        </h1>
        <p className="text-lg text-[#9CA3AF] max-w-2xl mx-auto animate-fade-in" style={{ animationDelay: "0.1s" }}>
          Plan AI-powered itineraries with flights and local experiences
        </p>
      </div>
    </section>
  );
}
