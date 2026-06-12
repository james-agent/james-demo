/**
 * @JAMES-INCEPTION-CARD
 * @card-id: JAMESD-6
 * @description: CRM opportunity MOCK table list with seller-oriented columns and navigation to detail.
 * MOCK only — not production; safe for another agent to use as a migration anchor.
 */
import { Component, inject, output } from '@angular/core';
import { RouterLink } from '@angular/router';

import { STAGE_LABELS } from './opportunity.models';
import { MockOpportunityService } from './mock-opportunity.service';

@Component({
  selector: 'app-opportunity-list-inception',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './opportunity-list-inception.component.html',
  styleUrl: './opportunity-list-inception.component.css',
})
export class OpportunityListInceptionComponent {
  private readonly mock = inject(MockOpportunityService);

  readonly toast = output<string>();

  get opportunities() {
    return this.mock.getFiltered();
  }

  stageLabel(stage: string): string {
    return STAGE_LABELS[stage as keyof typeof STAGE_LABELS] ?? stage;
  }

  formatCurrency(value: number): string {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
  }

  formatDate(value: string): string {
    if (!value) return '—';
    return new Intl.DateTimeFormat('pt-BR').format(new Date(value));
  }
}
