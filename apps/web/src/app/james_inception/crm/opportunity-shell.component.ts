/**
 * @JAMES-INCEPTION-CARD
 * @card-id: JAMESD-6
 * @description: CRM opportunity MOCK shell with role selector, table/Kanban toggle, and manager filters.
 * MOCK only — not production; safe for another agent to use as a migration anchor.
 */
import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';

import { MockRole, ViewMode } from './opportunity.models';
import { MockOpportunityService } from './mock-opportunity.service';
import { OpportunityKanbanInceptionComponent } from './opportunity-kanban-inception.component';
import { OpportunityListInceptionComponent } from './opportunity-list-inception.component';

@Component({
  selector: 'app-opportunity-shell',
  standalone: true,
  imports: [
    FormsModule,
    RouterLink,
    OpportunityListInceptionComponent,
    OpportunityKanbanInceptionComponent,
  ],
  templateUrl: './opportunity-shell.component.html',
  styleUrl: './opportunity-shell.component.css',
})
export class OpportunityShellComponent {
  private readonly mock = inject(MockOpportunityService);

  readonly role = this.mock.roleState;
  readonly viewMode = this.mock.viewModeState;
  readonly sellers = this.mock.sellers;
  readonly teams = this.mock.teams;

  sellerFilter = '';
  teamFilter = '';
  toastMessage: string | null = null;
  private toastTimer: ReturnType<typeof setTimeout> | null = null;

  setRole(role: MockRole): void {
    this.mock.setRole(role);
    this.sellerFilter = '';
    this.teamFilter = '';
  }

  setViewMode(mode: ViewMode): void {
    this.mock.setViewMode(mode);
  }

  onSellerFilterChange(): void {
    this.mock.setSellerFilter(this.sellerFilter);
  }

  onTeamFilterChange(): void {
    this.mock.setTeamFilter(this.teamFilter);
  }

  clearManagerFilters(): void {
    this.sellerFilter = '';
    this.teamFilter = '';
    this.mock.setSellerFilter('');
    this.mock.setTeamFilter('');
  }

  onToast(message: string): void {
    this.showToast(message);
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
