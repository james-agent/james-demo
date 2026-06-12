/**
 * @JAMES-INCEPTION-CARD
 * @card-id: JAMESD-6
 * @description: CRM opportunity MOCK detail view with main fields and product line totals.
 * MOCK only — not production; safe for another agent to use as a migration anchor.
 */
import { Component, inject, OnInit } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { computeLineTotal, ProductLine, STAGE_LABELS } from './opportunity.models';
import { MockOpportunityService } from './mock-opportunity.service';
import type { Opportunity } from './opportunity.models';

@Component({
  selector: 'app-opportunity-detail-inception',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './opportunity-detail-inception.component.html',
  styleUrl: './opportunity-detail-inception.component.css',
})
export class OpportunityDetailInceptionComponent implements OnInit {
  private readonly mock = inject(MockOpportunityService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  opportunity: Opportunity | null = null;
  toastMessage: string | null = null;
  private toastTimer: ReturnType<typeof setTimeout> | null = null;

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (!id) {
      this.redirectWithError();
      return;
    }
    const found = this.mock.getById(id);
    if (!found) {
      this.redirectWithError();
      return;
    }
    this.opportunity = found;
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

  lineTotal(line: ProductLine): number {
    return computeLineTotal(line);
  }

  private redirectWithError(): void {
    this.showToast('Oportunidade não encontrada');
    setTimeout(() => {
      this.router.navigate(['/inception_no_prod/crm/opportunities']);
    }, 800);
  }

  private showToast(message: string): void {
    this.toastMessage = message;
    if (this.toastTimer) {
      clearTimeout(this.toastTimer);
    }
    this.toastTimer = setTimeout(() => {
      this.toastMessage = null;
    }, 3000);
  }
}
