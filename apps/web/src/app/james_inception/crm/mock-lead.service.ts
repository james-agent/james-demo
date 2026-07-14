import { Injectable } from '@angular/core';
import { Observable, delay, of } from 'rxjs';

import { LeadListParams, LeadListResponse, LeadSummary } from './lead.models';

const VISIBLE_SEARCH_FIELDS: (keyof LeadSummary)[] = [
  'name',
  'email',
  'company',
  'country',
  'state',
  'status',
  'warmStatus',
  'phone',
  'segment',
  'accountOwner',
  'leadSource',
];

/** Local mock leads — same shape as Clients list mocks; no API. */
const MOCK_LEADS: LeadSummary[] = [
  {
    id: 'lead-001',
    name: 'Nina Alvarez',
    email: 'nina.alvarez@orbit.io',
    company: 'Orbit Media',
    country: 'United States',
    state: 'NY',
    status: 'New',
    warmStatus: 'Hot',
    inclusionDate: '2025-03-12T10:00:00.000Z',
    lastCommunicationDate: '2025-05-02T14:30:00.000Z',
    phone: '+1 212-555-3101',
    segment: 'Enterprise',
    accountOwner: 'Jordan Lee',
    leadSource: 'Webinar',
  },
  {
    id: 'lead-002',
    name: 'Omar Hassan',
    email: 'omar.hassan@desert.ae',
    company: 'Desert Labs',
    country: 'UAE',
    state: 'DU',
    status: 'Contacted',
    warmStatus: 'Warm',
    inclusionDate: '2025-02-20T10:00:00.000Z',
    lastCommunicationDate: '2025-04-18T11:15:00.000Z',
    phone: '+971 4 555 3202',
    segment: 'Mid-Market',
    accountOwner: 'Sara Nasser',
    leadSource: 'LinkedIn',
  },
  {
    id: 'lead-003',
    name: 'Priya Shah',
    email: 'priya.shah@mumbai.in',
    company: 'Mumbai Soft',
    country: 'India',
    state: 'MH',
    status: 'Qualified',
    warmStatus: 'Hot',
    inclusionDate: '2025-01-08T10:00:00.000Z',
    lastCommunicationDate: '2025-05-10T16:45:00.000Z',
    phone: '+91 22 5555 3303',
    segment: 'Enterprise',
    accountOwner: 'Raj Sharma',
    leadSource: 'Inbound',
  },
  {
    id: 'lead-004',
    name: 'Quinn Murphy',
    email: 'q.murphy@cork.ie',
    company: 'Cork Analytics',
    country: 'Ireland',
    state: 'C',
    status: 'New',
    warmStatus: 'Warm',
    inclusionDate: '2025-04-01T10:00:00.000Z',
    lastCommunicationDate: null,
    phone: '+353 21 555 3404',
    segment: 'SMB',
    accountOwner: 'Niamh Walsh',
    leadSource: 'Partner',
  },
  {
    id: 'lead-005',
    name: 'Rosa Mendes',
    email: 'rosa.mendes@lisboa.pt',
    company: 'Lisboa Cloud',
    country: 'Portugal',
    state: 'Lisbon',
    status: 'Contacted',
    warmStatus: 'Hot',
    inclusionDate: '2024-11-14T10:00:00.000Z',
    lastCommunicationDate: '2025-03-22T08:20:00.000Z',
    phone: '+351 21 555 3505',
    segment: 'Mid-Market',
    accountOwner: 'Rui Pereira',
    leadSource: 'Referral',
  },
  {
    id: 'lead-006',
    name: 'Soren Berg',
    email: 'soren.berg@oslo.no',
    company: 'Oslo Systems',
    country: 'Norway',
    state: 'Oslo',
    status: 'Nurturing',
    warmStatus: 'Warm',
    inclusionDate: '2024-09-09T10:00:00.000Z',
    lastCommunicationDate: '2024-12-01T13:00:00.000Z',
    phone: '+47 22 55 36 06',
    segment: 'SMB',
    accountOwner: 'Erik Johansson',
    leadSource: 'Cold Call',
  },
  {
    id: 'lead-007',
    name: 'Tara Nguyen',
    email: 'tara.nguyen@saigon.vn',
    company: 'Saigon Tech',
    country: 'Vietnam',
    state: 'HN',
    status: 'Qualified',
    warmStatus: 'Hot',
    inclusionDate: '2025-03-03T10:00:00.000Z',
    lastCommunicationDate: '2025-05-11T07:50:00.000Z',
    phone: '+84 28 5555 3707',
    segment: 'Enterprise',
    accountOwner: 'Min Park',
    leadSource: 'Trade Show',
  },
  {
    id: 'lead-008',
    name: 'Ulrich Keller',
    email: 'ulrich.keller@zurich.ch',
    company: 'Zurich Data',
    country: 'Switzerland',
    state: 'ZH',
    status: 'New',
    warmStatus: 'Warm',
    inclusionDate: '2025-05-01T10:00:00.000Z',
    lastCommunicationDate: '2025-05-05T12:00:00.000Z',
    phone: '+41 44 555 3808',
    segment: 'Mid-Market',
    accountOwner: 'Hans Weber',
    leadSource: 'Inbound',
  },
  {
    id: 'lead-009',
    name: 'Vera Costa',
    email: 'vera.costa@porto.br',
    company: 'Porto Digital',
    country: 'Brazil',
    state: 'RS',
    status: 'Contacted',
    warmStatus: 'Hot',
    inclusionDate: '2025-02-14T10:00:00.000Z',
    lastCommunicationDate: '2025-04-05T17:10:00.000Z',
    phone: '+55 51 95555-3909',
    segment: 'Enterprise',
    accountOwner: 'Ana Costa',
    leadSource: 'Webinar',
  },
  {
    id: 'lead-010',
    name: 'Will Parker',
    email: 'will.parker@austin.us',
    company: 'Austin Peak',
    country: 'United States',
    state: 'TX',
    status: 'Qualified',
    warmStatus: 'Warm',
    inclusionDate: '2024-12-19T10:00:00.000Z',
    lastCommunicationDate: '2025-05-09T09:30:00.000Z',
    phone: '+1 512-555-4010',
    segment: 'Mid-Market',
    accountOwner: 'Jordan Lee',
    leadSource: 'Referral',
  },
];

@Injectable({ providedIn: 'root' })
export class MockLeadService {
  listLeads(params: LeadListParams): Observable<LeadListResponse> {
    const filtered = this.filter(params);
    const response = this.paginate(filtered, params.page, params.pageSize);
    // Brief delay so the loading state mirrors the Clients list UX.
    return of(response).pipe(delay(150));
  }

  private filter(params: LeadListParams): LeadSummary[] {
    let results = [...MOCK_LEADS];
    const name = params.name?.trim().toLowerCase();
    const email = params.email?.trim().toLowerCase();
    const q = params.q?.trim().toLowerCase();

    if (name) {
      results = results.filter((lead) => lead.name.toLowerCase().includes(name));
    }
    if (email) {
      results = results.filter((lead) => lead.email.toLowerCase().includes(email));
    }
    if (q) {
      results = results.filter((lead) => this.matchesFreeSearch(lead, q));
    }
    return results;
  }

  private matchesFreeSearch(lead: LeadSummary, needle: string): boolean {
    for (const field of VISIBLE_SEARCH_FIELDS) {
      const value = lead[field];
      if (value != null && String(value).toLowerCase().includes(needle)) {
        return true;
      }
    }
    if (lead.lastCommunicationDate?.toLowerCase().includes(needle)) {
      return true;
    }
    return lead.inclusionDate.toLowerCase().includes(needle);
  }

  private paginate(leads: LeadSummary[], page: number, pageSize: number): LeadListResponse {
    const totalItems = leads.length;
    const totalPages = totalItems === 0 ? 0 : Math.max(1, Math.ceil(totalItems / pageSize));
    if (totalItems === 0) {
      return { items: [], page: 1, pageSize, totalItems: 0, totalPages: 0 };
    }
    const safePage = Math.min(Math.max(page, 1), totalPages);
    const start = (safePage - 1) * pageSize;
    return {
      items: leads.slice(start, start + pageSize),
      page: safePage,
      pageSize,
      totalItems,
      totalPages,
    };
  }
}
