import { Download, Mail, Loader } from 'lucide-react';
import { useState } from 'react';
import { type Trip } from '../services/api';
import { downloadTripPDF } from '../services/pdfService';

interface ExportButtonProps {
  trip: Trip;
  onEmailClick?: () => void;
}

const ExportButton = ({ trip, onEmailClick }: ExportButtonProps) => {
  const [downloading, setDownloading] = useState(false);

  const handleDownloadPDF = async () => {
    setDownloading(true);
    try {
      downloadTripPDF(trip);
      console.log('✅ PDF downloaded successfully');
    } catch (error) {
      console.error('❌ Error downloading PDF:', error);
      alert('Failed to download PDF');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="flex gap-3">
      {/* Download PDF Button */}
      <button
        onClick={handleDownloadPDF}
        disabled={downloading}
        className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold transition-all cursor-pointer ${
          downloading
            ? 'bg-[#6B7280] cursor-not-allowed text-white/50'
            : 'bg-[#38BDF8] text-white hover:bg-[#0EA5E9] hover:scale-105 active:scale-95'
        }`}
        title="Download itinerary as PDF"
      >
        {downloading ? (
          <>
            <Loader className="w-5 h-5 animate-spin" />
            Generating PDF...
          </>
        ) : (
          <>
            <Download className="w-5 h-5" />
            Download PDF
          </>
        )}
      </button>

      {/* Email Button (Optional) */}
      <button
        onClick={onEmailClick}
        className="flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-semibold text-white bg-[#10B981] hover:bg-[#059669] hover:scale-[1.02] active:scale-95 transition-all shadow-lg shadow-[#10B981]/20 cursor-pointer"
        title="Email itinerary"
      >
        <Mail className="w-5 h-5" />
        Email Itinerary
      </button>
    </div>
  );
};

export default ExportButton;
