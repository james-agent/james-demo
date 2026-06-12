import { TestBed } from '@angular/core/testing';

import { MockOpportunityService } from './mock-opportunity.service';

describe('MockOpportunityService', () => {
  let service: MockOpportunityService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(MockOpportunityService);
    service.setRole('vendedor');
  });

  it('filters opportunities for vendedor role to simulated seller only', () => {
    const filtered = service.getFiltered();
    expect(filtered.length).toBeGreaterThan(0);
    expect(filtered.every((o) => o.owner === service.simulatedSeller)).toBe(true);
  });

  it('updates stage via updateStage', () => {
    const target = service.getFiltered().find((o) => o.stage === 'qualificacao');
    expect(target).toBeTruthy();
    const ok = service.updateStage(target!.id, 'proposta');
    expect(ok).toBe(true);
    expect(service.getById(target!.id)?.stage).toBe('proposta');
  });

  it('returns false from updateStage for unknown id', () => {
    expect(service.updateStage('missing-id', 'proposta')).toBe(false);
  });

  it('creates and updates opportunities', () => {
    const created = service.create({
      name: 'Test Opp',
      account: 'Acct',
      value: 1000,
      stage: 'qualificacao',
      probability: 10,
      closeDate: '2026-12-01',
      owner: 'Ana Silva',
      ownerTeam: 'Norte',
      description: '',
      nextStep: '',
      productLines: [{ id: 'pl-t', item: 'Item', quantity: 1, unitPrice: 1000 }],
    });

    expect(created.id).toBeTruthy();
    const updated = service.update(created.id, { name: 'Updated Opp' });
    expect(updated?.name).toBe('Updated Opp');
  });

  it('filters by seller when gerente role and seller filter set', () => {
    service.setRole('gerente');
    service.setSellerFilter('Bruno Costa');
    const filtered = service.getFiltered();
    expect(filtered.every((o) => o.owner === 'Bruno Costa')).toBe(true);
  });

  it('defaults view mode by role', () => {
    service.setRole('vendedor');
    expect(service.viewModeState()).toBe('table');
    service.setRole('gerente');
    expect(service.viewModeState()).toBe('kanban');
  });
});
