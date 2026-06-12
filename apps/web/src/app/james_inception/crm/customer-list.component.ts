/**
 * @JAMES-INCEPTION-CARD
 * @card-id: JAMESD-5
 * @description: CRM customer inception listing with debounced filters, pagination, and ephemeral session overlay.
 * MOCK only — not production; safe for another agent to use as a migration anchor.
 */
import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';

import { CustomerDetailModalComponent } from './customer-detail-modal.component';
import { CrmCustomerApiService } from './crm-customer-api.service';
import { CrmI18nService } from './crm-i18n.service';
import { CrmSessionOverlayService } from './crm-session-overlay.service';
import { CrmLocale, CustomerSummary } from './crm.models';

type LoadState = 'idle' | 'loading' | 'error' | 'empty' | 'ready';

@Component({
  selector: 'app-customer-list',
  standalone: true,
  imports: [FormsModule, CustomerDetailModalComponent],
  templateUrl: './customer-list.component.html',
  styleUrl: './customer-list.component.css',
})
export class CustomerListComponent implements OnInit, OnDestroy {
  readonly i18n = inject(CrmI18nService);
  private readonly api = inject(CrmCustomerApiService);
  private readonly overlay = inject(CrmSessionOverlayService);

  readonly pageSizes = [10, 25, 50];

  filterName = '';
  filterEmail = '';
  filterQ = '';
  page = 1;
  pageSize = 10;

  customers: CustomerSummary[] = [];
  totalItems = 0;
  totalPages = 0;
  loadState: LoadState = 'idle';
  emptyMessage = '';

  modalOpen = false;
  selectedCustomerId: string | null = null;
  toastMessage: string | null = null;

  private debounceTimer: ReturnType<typeof setTimeout> | null = null;
  private listSubscription: Subscription | null = null;
  private toastTimer: ReturnType<typeof setTimeout> | null = null;

  ngOnInit(): void {
    this.loadCustomers();
  }

  ngOnDestroy(): void {
    this.clearDebounce();
    this.cancelListRequest();
  }

  onFilterInput(): void {
    this.clearDebounce();
    this.debounceTimer = setTimeout(() => {
      this.page = 1;
      this.loadCustomers();
    }, 400);
  }

  clearFilters(): void {
    this.filterName = '';
    this.filterEmail = '';
    this.filterQ = '';
    this.page = 1;
    this.loadCustomers();
  }

  changePage(next: number): void {
    if (next < 1 || next > this.totalPages || next === this.page) {
      return;
    }
    this.page = next;
    this.loadCustomers();
  }

  changePageSize(size: number): void {
    this.pageSize = size;
    this.page = 1;
    this.loadCustomers();
  }

  openDetail(customerId: string): void {
    this.selectedCustomerId = customerId;
    this.modalOpen = true;
  }

  closeModal(): void {
    this.modalOpen = false;
    this.selectedCustomerId = null;
  }

  onCustomerUpdated(): void {
    this.customers = this.customers.map((c) => this.overlay.applyToSummary(c));
  }

  onModalToast(message: string): void {
    this.showToast(message);
  }

  onLocaleChange(locale: CrmLocale): void {
    this.i18n.setLocale(locale);
    this.customers = this.customers.map((c) => this.overlay.applyToSummary(c));
  }

  retry(): void {
    this.loadCustomers();
  }

  displayValue(value: string | null | undefined): string {
    return value && value.trim() ? value : '—';
  }

  private loadCustomers(): void {
    this.cancelListRequest();
    this.loadState = 'loading';
    this.emptyMessage = '';

    this.listSubscription = this.api
      .listCustomers({
        page: this.page,
        pageSize: this.pageSize,
        name: this.filterName,
        email: this.filterEmail,
        q: this.filterQ,
      })
      .subscribe({
        next: (response) => {
          this.customers = response.items.map((c) => this.overlay.applyToSummary(c));
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
          this.customers = [];
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
