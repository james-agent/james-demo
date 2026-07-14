/**
 * @card-id: JAMESD-7
 * @description: CRM Leads list — mock-only UI mirroring the Clients/Accounts list layout.
 */
import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';

import { CrmLocale } from './crm.models';
import { LeadI18nService } from './lead-i18n.service';
import { LeadSummary } from './lead.models';
import { MockLeadService } from './mock-lead.service';

type LoadState = 'idle' | 'loading' | 'error' | 'empty' | 'ready';

@Component({
  selector: 'app-lead-list',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './lead-list.component.html',
  styleUrl: './customer-list.component.css',
})
export class LeadListComponent implements OnInit, OnDestroy {
  readonly i18n = inject(LeadI18nService);
  private readonly mock = inject(MockLeadService);

  readonly pageSizes = [10, 25, 50];

  filterName = '';
  filterEmail = '';
  filterQ = '';
  page = 1;
  pageSize = 10;

  leads: LeadSummary[] = [];
  totalItems = 0;
  totalPages = 0;
  loadState: LoadState = 'idle';
  emptyMessage = '';

  toastMessage: string | null = null;

  private debounceTimer: ReturnType<typeof setTimeout> | null = null;
  private listSubscription: Subscription | null = null;
  private toastTimer: ReturnType<typeof setTimeout> | null = null;

  ngOnInit(): void {
    this.loadLeads();
  }

  ngOnDestroy(): void {
    this.clearDebounce();
    this.cancelListRequest();
  }

  onFilterInput(): void {
    this.clearDebounce();
    this.debounceTimer = setTimeout(() => {
      this.page = 1;
      this.loadLeads();
    }, 400);
  }

  clearFilters(): void {
    this.filterName = '';
    this.filterEmail = '';
    this.filterQ = '';
    this.page = 1;
    this.loadLeads();
  }

  changePage(next: number): void {
    if (next < 1 || next > this.totalPages || next === this.page) {
      return;
    }
    this.page = next;
    this.loadLeads();
  }

  changePageSize(size: number): void {
    this.pageSize = size;
    this.page = 1;
    this.loadLeads();
  }

  /** Non-functional stub — Clients list opens a detail modal; Leads has list-only scope. */
  openDetail(_leadId: string): void {
    this.showToast(this.i18n.t('detailStub'));
  }

  onLocaleChange(locale: CrmLocale): void {
    this.i18n.setLocale(locale);
  }

  retry(): void {
    this.loadLeads();
  }

  displayValue(value: string | null | undefined): string {
    return value && value.trim() ? value : '—';
  }

  private loadLeads(): void {
    this.cancelListRequest();
    this.loadState = 'loading';
    this.emptyMessage = '';

    this.listSubscription = this.mock
      .listLeads({
        page: this.page,
        pageSize: this.pageSize,
        name: this.filterName,
        email: this.filterEmail,
        q: this.filterQ,
      })
      .subscribe({
        next: (response) => {
          this.leads = response.items;
          this.totalItems = response.totalItems;
          this.totalPages = response.totalPages;
          this.page = response.page;

          if (this.totalItems === 0) {
            this.loadState = 'empty';
            const hasFilters =
              this.filterName.trim() || this.filterEmail.trim() || this.filterQ.trim();
            this.emptyMessage = hasFilters ? this.i18n.t('emptyNoMatch') : this.i18n.t('emptyNoData');
          } else {
            this.loadState = 'ready';
          }
        },
        error: () => {
          this.leads = [];
          this.loadState = 'error';
        },
      });
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

  private clearDebounce(): void {
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = null;
    }
  }

  private cancelListRequest(): void {
    this.listSubscription?.unsubscribe();
    this.listSubscription = null;
  }
}
