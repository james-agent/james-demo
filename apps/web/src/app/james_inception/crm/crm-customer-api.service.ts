import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { CustomerDetail, CustomerListParams, CustomerListResponse } from './crm.models';

@Injectable({ providedIn: 'root' })
export class CrmCustomerApiService {
  private readonly baseUrl = '/api/v1/crm';

  constructor(private readonly http: HttpClient) {}

  listCustomers(params: CustomerListParams): Observable<CustomerListResponse> {
    let httpParams = new HttpParams()
      .set('page', String(params.page))
      .set('pageSize', String(params.pageSize));
    if (params.name?.trim()) {
      httpParams = httpParams.set('name', params.name.trim());
    }
    if (params.email?.trim()) {
      httpParams = httpParams.set('email', params.email.trim());
    }
    if (params.q?.trim()) {
      httpParams = httpParams.set('q', params.q.trim());
    }
    return this.http.get<CustomerListResponse>(`${this.baseUrl}/customers`, { params: httpParams });
  }

  getCustomer(id: string): Observable<CustomerDetail> {
    return this.http.get<CustomerDetail>(`${this.baseUrl}/customers/${id}`);
  }
}
