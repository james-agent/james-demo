import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';

import { MockOpportunityService } from './mock-opportunity.service';
import { OpportunityFormInceptionComponent } from './opportunity-form-inception.component';

describe('OpportunityFormInceptionComponent', () => {
  let fixture: ComponentFixture<OpportunityFormInceptionComponent>;
  let component: OpportunityFormInceptionComponent;
  let mockService: MockOpportunityService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [OpportunityFormInceptionComponent],
      providers: [
        provideRouter([
          { path: 'inception_no_prod/crm/opportunities', component: OpportunityFormInceptionComponent },
          { path: 'inception_no_prod/crm/opportunities/new', component: OpportunityFormInceptionComponent },
        ]),
      ],
    }).compileComponents();

    mockService = TestBed.inject(MockOpportunityService);
    fixture = TestBed.createComponent(OpportunityFormInceptionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('blocks save when nome is empty', () => {
    component.form.patchValue({ name: '' });
    component.save();
    expect(component.form.invalid).toBe(true);
    expect(component.toastMessage).toBe('Corrija os campos obrigatórios');
  });

  it('calculates line and grand totals', () => {
    component.addProductLine();
    const line = component.productLines.at(0);
    line.patchValue({ item: 'Produto', quantity: 2, unitPrice: 50 });
    expect(component.lineTotalAt(0)).toBe(100);
    expect(component.grandTotal()).toBe(100);
  });

  it('creates opportunity on valid save', fakeAsync(() => {
    const router = TestBed.inject(Router);
    const navigateSpy = spyOn(router, 'navigate').and.returnValue(Promise.resolve(true));

    component.form.patchValue({
      name: 'Nova Opp Test',
      account: 'Conta',
      stage: 'qualificacao',
      probability: 30,
      closeDate: '2026-12-01',
      owner: mockService.simulatedSeller,
      ownerTeam: 'Norte',
    });
    component.productLines.at(0).patchValue({
      item: 'Item',
      quantity: 1,
      unitPrice: 500,
    });

    component.save();
    tick(700);

    const created = mockService.getById(
      mockService
        .getFiltered()
        .find((o) => o.name === 'Nova Opp Test')?.id ?? '',
    );
    expect(created?.name).toBe('Nova Opp Test');
    expect(navigateSpy).toHaveBeenCalled();
  }));
});
