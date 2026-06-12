export type WarmStatus = 'Hot' | 'Warm';
export type CrmLocale = 'en-US' | 'pt-BR';

export interface CustomerComment {
  id: string;
  text: string;
  author: string;
  createdAt: string;
  isSession?: boolean;
}

export interface CustomerSummary {
  id: string;
  name: string;
  email: string;
  company: string;
  country: string;
  state: string;
  status: string;
  warmStatus: WarmStatus;
  inclusionDate: string;
  lastCommunicationDate: string | null;
  phone: string;
  segment: string;
  accountOwner: string;
  leadSource: string;
}

export interface CustomerDetail extends CustomerSummary {
  comments: CustomerComment[];
}

export interface CustomerListResponse {
  items: CustomerSummary[];
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
}

export interface CustomerListParams {
  page: number;
  pageSize: number;
  name?: string;
  email?: string;
  q?: string;
}
