/**
 * @JAMES-INCEPTION-CARD
 * @card-id: JAMESD-6
 * @description: CRM opportunity MOCK Kanban with drag-and-drop stage changes and column totals.
 * MOCK only — not production; safe for another agent to use as a migration anchor.
 */
import { Component, effect, inject, output } from '@angular/core';
import { RouterLink } from '@angular/router';
import {
  CdkDragDrop,
  DragDropModule,
  moveItemInArray,
  transferArrayItem,
} from '@angular/cdk/drag-drop';

import {
  OPPORTUNITY_STAGES,
  Opportunity,
  OpportunityStage,
  STAGE_LABELS,
} from './opportunity.models';
import { MockOpportunityService } from './mock-opportunity.service';

@Component({
  selector: 'app-opportunity-kanban-inception',
  standalone: true,
  imports: [RouterLink, DragDropModule],
  templateUrl: './opportunity-kanban-inception.component.html',
  styleUrl: './opportunity-kanban-inception.component.css',
})
export class OpportunityKanbanInceptionComponent {
  private readonly mock = inject(MockOpportunityService);

  readonly toast = output<string>();
  readonly stages = OPPORTUNITY_STAGES;

  stageColumns: Record<OpportunityStage, Opportunity[]> = this.buildColumns();

  constructor() {
    effect(() => {
      this.mock.roleState();
      this.mock.sellerFilterState();
      this.mock.teamFilterState();
      this.refreshColumns();
    });
  }

  stageLabel(stage: OpportunityStage): string {
    return STAGE_LABELS[stage];
  }

  formatCurrency(value: number): string {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
  }

  columnTotal(stage: OpportunityStage): number {
    return this.stageColumns[stage].reduce((sum, o) => sum + o.value, 0);
  }

  refreshColumns(): void {
    this.stageColumns = this.buildColumns();
  }

  isEmpty(): boolean {
    return this.stages.every((s) => this.stageColumns[s].length === 0);
  }

  onDrop(event: CdkDragDrop<Opportunity[]>): void {
    const targetStage = event.container.id as OpportunityStage;
    if (!OPPORTUNITY_STAGES.includes(targetStage)) {
      return;
    }

    if (event.previousContainer === event.container) {
      moveItemInArray(event.container.data, event.previousIndex, event.currentIndex);
      return;
    }

    const opp = event.previousContainer.data[event.previousIndex];
    const updated = this.mock.updateStage(opp.id, targetStage);
    if (!updated) {
      return;
    }

    transferArrayItem(
      event.previousContainer.data,
      event.container.data,
      event.previousIndex,
      event.currentIndex,
    );

    this.toast.emit('Estágio atualizado');
    this.refreshColumns();
  }

  private buildColumns(): Record<OpportunityStage, Opportunity[]> {
    const filtered = this.mock.getFiltered();
    const columns = {} as Record<OpportunityStage, Opportunity[]>;
    for (const stage of OPPORTUNITY_STAGES) {
      columns[stage] = filtered.filter((o) => o.stage === stage);
    }
    return columns;
  }
}
