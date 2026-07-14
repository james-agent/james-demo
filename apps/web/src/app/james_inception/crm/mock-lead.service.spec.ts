import { TestBed } from '@angular/core/testing';
import { firstValueFrom } from 'rxjs';

import { MockLeadService } from './mock-lead.service';

describe('MockLeadService', () => {
  let service: MockLeadService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(MockLeadService);
  });

  it('returns paginated mock leads without HTTP', async () => {
    const response = await firstValueFrom(
      service.listLeads({ page: 1, pageSize: 10 }),
    );

    expect(response.totalItems).toBe(10);
    expect(response.items.length).toBe(10);
    expect(response.items[0].id).toMatch(/^lead-/);
  });

  it('filters by name using local mock data', async () => {
    const response = await firstValueFrom(
      service.listLeads({ page: 1, pageSize: 10, name: 'Nina' }),
    );

    expect(response.totalItems).toBe(1);
    expect(response.items[0].name).toBe('Nina Alvarez');
  });
});
