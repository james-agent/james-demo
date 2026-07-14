import { CustomerListParams, CustomerListResponse, CustomerSummary } from './crm.models';

/** Lead list rows mirror the Clients/Accounts summary schema. */
export type LeadSummary = CustomerSummary;

export type LeadListResponse = CustomerListResponse;

export type LeadListParams = CustomerListParams;
