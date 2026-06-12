import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { CdkDragDrop } from '@angular/cdk/drag-drop';

import { Opportunity } from './opportunity.models';
import { MockOpportunityService } from './mock-opportunity.service';
import { OpportunityKanbanInceptionComponent } from './opportunity-kanban-inception.component';

describe('OpportunityKanbanInceptionComponent', () => {
  let fixture: ComponentFixture<OpportunityKanbanInceptionComponent>;
  let component: OpportunityKanbanInceptionComponent;
  let mockService: MockOpportunityService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [OpportunityKanbanInceptionComponent],
      providers: [provideRouter([])],
    }).compileComponents();

    mockService = TestBed.inject(MockOpportunityService);
    mockService.setRole('gerente');

    fixture = TestBed.createComponent(OpportunityKanbanInceptionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('emits toast and updates mock stage on cross-column drop', () => {
    const opp = mockService.getFiltered().find((o) => o.stage === 'qualificacao');
    expect(opp).toBeTruthy();

    const sourceData = [opp!];
    const targetData: Opportunity[] = [];
    const event = {
      previousContainer: { id: 'qualificacao', data: sourceData },
      container: { id: 'proposta', data: targetData },
      previousIndex: 0,
      currentIndex: 0,
      item: { data: opp },
    } as unknown as CdkDragDrop<Opportunity[]>;

    let toastText = '';
    component.toast.subscribe((msg) => (toastText = msg));

    component.onDrop(event);

    expect(mockService.getById(opp!.id)?.stage).toBe('proposta');
    expect(toastText).toBe('Estágio atualizado');
  });

  it('does not update mock when updateStage fails', () => {
    const fakeOpp = {
      id: 'invalid-opp',
      name: 'X',
      account: 'Y',
      value: 1,
      stage: 'qualificacao' as const,
      probability: 1,
      closeDate: '',
      owner: 'Ana Silva',
      ownerTeam: 'Norte',
      description: '',
      nextStep: '',
      productLines: [],
    };

    const sourceData = [fakeOpp];
    const targetData: Opportunity[] = [];
    const event = {
      previousContainer: { id: 'qualificacao', data: sourceData },
      container: { id: 'proposta', data: targetData },
      previousIndex: 0,
      currentIndex: 0,
      item: { data: fakeOpp },
    } as unknown as CdkDragDrop<Opportunity[]>;

    component.onDrop(event);

    expect(targetData.length).toBe(0);
    expect(sourceData.length).toBe(1);
  });
});
