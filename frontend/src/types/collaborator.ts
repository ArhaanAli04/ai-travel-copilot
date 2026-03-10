export type CollaboratorRole = 'viewer' | 'editor';
export type CollaboratorStatus = 'pending' | 'accepted' | 'declined';

export interface Collaborator {
  id: number;
  trip_id: number;
  invited_by_user_id: number;
  email: string;
  clerk_user_id: string | null;
  role: CollaboratorRole;
  status: CollaboratorStatus;
  invite_token: string;
  invited_at: string;
  accepted_at: string | null;
}

export interface CollaboratorListResponse {
  trip_id: number;
  collaborators: Collaborator[];
  total: number;
}

export interface InvitePreviewResponse {
  token: string;
  trip_id: number;
  trip_title: string;
  trip_origin: string;
  destinations: string[];
  start_date: string;
  end_date: string;
  invited_by_name: string | null;
  role: CollaboratorRole;
  status: CollaboratorStatus;
}

export interface AcceptInviteResponse {
  success: boolean;
  message: string;
  trip_id: number;
  trip_title: string;
  role: CollaboratorRole;
}
