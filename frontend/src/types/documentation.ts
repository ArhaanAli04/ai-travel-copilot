// ─────────────────────────────────────────────────────────────────────────────
// Documentation Types — mirrors backend TripDocumentation model exactly
// ─────────────────────────────────────────────────────────────────────────────


// ── Document Checklist ───────────────────────────────────────────────────────

export interface ChecklistItem {
  item: string;
  required: boolean;
  notes: string;
}

export interface DocumentChecklist {
  destination: string;
  visa_type: string;
  visa_cost: string;
  processing_days: string;
  apply_url: string;
  procedure: string;
  checklist_items: ChecklistItem[];
}


// ── Entry Requirements ───────────────────────────────────────────────────────

export interface EntryRequirementItem {
  category: 'Health' | 'Customs' | 'Restricted Items' | 'Minor Travel' | 'Currency' | string;
  description: string;
  details: string;
}

export interface EntryRequirements {
  destination: string;
  items: EntryRequirementItem[];
}


// ── Legal Advisories ─────────────────────────────────────────────────────────

export type AdvisorySeverity = 'critical' | 'warning' | 'info';

export interface Advisory {
  severity: AdvisorySeverity;
  category: string;
  description: string;
}

export interface LegalAdvisories {
  destination: string;
  advisories: Advisory[];
}


// ── Emergency Contacts ───────────────────────────────────────────────────────

export interface HospitalRecommendation {
  name: string;
  address: string;
  phone: string;
  notes: string;
}

export interface EmergencyContacts {
  destination: string;
  police: string;
  ambulance: string;
  fire: string;
  general_emergency: string;
  embassy_phone: string;
  embassy_address: string;
  embassy_website: string;
  hospital_recommendations: HospitalRecommendation[];
  travel_advisory_level: string;
  travel_advisory_source: string;
}


// ── Top-level Response ───────────────────────────────────────────────────────

export interface DocumentationResponse {
  id: number;
  trip_id: number;
  origin_country: string;
  document_checklist: DocumentChecklist[];
  entry_requirements: EntryRequirements[];
  legal_advisories: LegalAdvisories[];
  emergency_contacts: EmergencyContacts[];
  generated_at: string;
  created_at: string;
  updated_at: string | null;
}


// ── Status Response ──────────────────────────────────────────────────────────

export interface DocumentationStatusResponse {
  trip_id: number;
  exists: boolean;
  generated_at: string | null;
}
