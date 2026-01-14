import jsPDF from 'jspdf';
import { type Trip,type TripDay,type Activity } from './api';

export const generateTripPDF = (trip: Trip) => {
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4'
  });

  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 15;
  const contentWidth = pageWidth - margin * 2;
  let yPosition = margin;

  // Helper function to check if we need a new page
  const checkPageBreak = (lineHeight: number) => {
    if (yPosition + lineHeight > pageHeight - margin) {
      doc.addPage();
      yPosition = margin;
    }
  };

  // Helper function to add text with wrapping
  const addWrappedText = (
    text: string,
    fontSize: number,
    isBold: boolean = false,
    lineHeight: number = 7
  ) => {
    doc.setFontSize(fontSize);
    doc.setFont('helvetica', isBold ? 'bold' : 'normal');
    
    const textStr = String(text || '').trim();
    if (!textStr) return;
    
    const lines = doc.splitTextToSize(textStr, contentWidth);
    const totalHeight = lines.length * lineHeight;
    
    checkPageBreak(totalHeight);
    doc.text(lines, margin, yPosition);
    yPosition += totalHeight;
  };

  // ===== TITLE SECTION =====
  doc.setFontSize(24);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(56, 189, 248);
  checkPageBreak(15);
  doc.text('Trip Itinerary', margin, yPosition); // REMOVED: ✈️
  yPosition += 15;

  // ===== HEADER LINE =====
  doc.setDrawColor(56, 189, 248);
  doc.setLineWidth(0.5);
  doc.line(margin, yPosition, pageWidth - margin, yPosition);
  yPosition += 8;

  // ===== TRIP TITLE =====
  doc.setTextColor(0, 0, 0);
  doc.setFontSize(18);
  doc.setFont('helvetica', 'bold');
  const tripTitleLines = doc.splitTextToSize(String(trip.title || 'Untitled Trip'), contentWidth);
  doc.text(tripTitleLines, margin, yPosition);
  yPosition += tripTitleLines.length * 7 + 5;

  // ===== TRIP DETAILS (Origins & Destinations) =====
  doc.setTextColor(0, 0, 0);
  doc.setFontSize(11);
  doc.setFont('helvetica', 'normal');

  const origin = trip.origin || 'Unknown';
  const dests = trip.destinations && trip.destinations.length > 0 
    ? trip.destinations.join(', ') 
    : 'Unknown';
  
  addWrappedText(
    `From: ${origin} -> ${dests}`, // REMOVED: 📍 and changed arrow
    11,
    false,
    6
  );

  // ===== DATES =====
  const startDate = trip.start_date 
    ? new Date(trip.start_date).toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
      })
    : 'Not set';
  
  const endDate = trip.end_date 
    ? new Date(trip.end_date).toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
      })
    : 'Not set';

  addWrappedText(
    `${startDate} - ${endDate}`, // REMOVED: 📅
    11,
    false,
    6
  );

  // ===== TRAVELERS & BUDGET =====
  const travelers = trip.traveler_count || 1;
  const budgetStr = trip.budget 
    ? `$${trip.budget} ${trip.budget_currency || 'USD'}`
    : 'Not specified';

  addWrappedText(
    `Travelers: ${travelers} | Budget: ${budgetStr}`, // REMOVED: 👥 💰
    11,
    false,
    6
  );

  // ===== INTERESTS =====
  if (trip.interests && trip.interests.length > 0) {
    const interestStr = Array.isArray(trip.interests) 
      ? trip.interests.join(', ')
      : String(trip.interests);
    
    addWrappedText(
      `Interests: ${interestStr}`, // REMOVED: 🎯
      11,
      false,
      6
    );
  }

  yPosition += 10;

  // ===== ITINERARY SECTION =====
  if (trip.days && trip.days.length > 0) {
    trip.days.forEach((day: TripDay, dayIndex: number) => {
      checkPageBreak(12);

      // Day header background
      doc.setFillColor(56, 189, 248);
      doc.rect(margin, yPosition - 4, contentWidth, 10, 'F');
      
      // Day header text
      doc.setTextColor(255, 255, 255);
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(13);
      
      const dayCity = day.city || 'TBA';
      const dayDate = day.date 
        ? new Date(day.date).toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
          })
        : 'Date TBA';
      
      const dayText = `Day ${day.day_number || dayIndex + 1} - ${dayCity} (${dayDate})`;
      
      doc.text(dayText, margin + 3, yPosition + 3);
      yPosition += 12;

      // Day theme
      if (day.theme) {
        doc.setTextColor(100, 100, 100);
        doc.setFontSize(10);
        doc.setFont('helvetica', 'italic');
        const themeLines = doc.splitTextToSize(`Theme: ${String(day.theme)}`, contentWidth - 4);
        doc.text(themeLines, margin + 2, yPosition);
        yPosition += themeLines.length * 5 + 2;
      }

      // Activities
      if (day.activities && day.activities.length > 0) {
        doc.setTextColor(0, 0, 0);
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(10);

        day.activities.forEach((activity: Activity, actIndex: number) => {
          checkPageBreak(8);

          // Activity time
          const timeStr = activity.start_time && activity.end_time
            ? `${activity.start_time} - ${activity.end_time}`
            : activity.start_time 
              ? `${activity.start_time} onwards`
              : 'Time TBA';
          
          // Activity title with time
          const activityTitle = `${actIndex + 1}. ${String(activity.title || 'Activity')} (${timeStr})`;
          
          doc.setFont('helvetica', 'bold');
          const titleLines = doc.splitTextToSize(activityTitle, contentWidth - 4);
          doc.text(titleLines, margin + 2, yPosition);
          yPosition += titleLines.length * 6;

          // Activity description
          if (activity.description) {
            doc.setFont('helvetica', 'normal');
            const descLines = doc.splitTextToSize(
              String(activity.description), 
              contentWidth - 4
            );
            doc.text(descLines, margin + 4, yPosition);
            yPosition += descLines.length * 5;
          }

          yPosition += 2;
        });
      } else {
        // No activities message
        doc.setTextColor(150, 150, 150);
        doc.setFontSize(9);
        doc.setFont('helvetica', 'italic');
        doc.text('No activities planned for this day', margin + 2, yPosition);
        yPosition += 6;
      }

      yPosition += 5;
    });
  } else {
    // No days message
    doc.setTextColor(150, 150, 150);
    doc.setFontSize(11);
    doc.setFont('helvetica', 'italic');
    doc.text('No itinerary generated yet', margin, yPosition);
    yPosition += 10;
  }

  // ===== FOOTER =====
  yPosition = pageHeight - 15;
  doc.setTextColor(150, 150, 150);
  doc.setFontSize(8);
  doc.setFont('helvetica', 'italic');
  doc.text(
    `Generated by AI Travel Copilot on ${new Date().toLocaleDateString()}`,
    margin,
    yPosition
  );

  // ===== PAGE NUMBERS =====
  const pageCount = doc.getNumberOfPages();
  for (let i = 1; i <= pageCount; i++) {
    doc.setPage(i);
    doc.setFontSize(8);
    doc.setTextColor(150, 150, 150);
    doc.text(
      `Page ${i} of ${pageCount}`,
      pageWidth - margin - 20,
      pageHeight - 10
    );
  }

  return doc;
};

// Download PDF
export const downloadTripPDF = (trip: Trip) => {
  const doc = generateTripPDF(trip);
  const fileName = `${String(trip.title || 'Trip').replace(/\s+/g, '_')}_itinerary.pdf`;
  doc.save(fileName);
};

// Get PDF as Blob (for email)
export const getTripPDFBlob = (trip: Trip): Blob => {
  const doc = generateTripPDF(trip);
  return doc.output('blob');
};
