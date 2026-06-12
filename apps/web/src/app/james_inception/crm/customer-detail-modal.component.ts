/**
 * @JAMES-INCEPTION-CARD
 * @card-id: JAMESD-5
 * @description: CRM customer detail modal with ephemeral comments and warm status toggle.
 * MOCK only — not production; safe for another agent to use as a migration anchor.
 */
import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { CrmCustomerApiService } from './crm-customer-api.service';
import { CrmI18nService } from './crm-i18n.service';
import { CrmSessionOverlayService } from './crm-session-overlay.service';
import { CustomerDetail, WarmStatus } from './crm.models';

@Component({
  selector: 'app-customer-detail-modal',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './customer-detail-modal.component.html',
  styleUrl: './customer-detail-modal.component.css',
})
export class CustomerDetailModalComponent implements OnChanges {
  @Input({ required: true }) customerId: string | null = null;
  @Input() open = false;
  @Output() closed = new EventEmitter<void>();
  @Output() customerUpdated = new EventEmitter<void>();
  @Output() toast = new EventEmitter<string>();

  readonly i18n = inject(CrmI18nService);
  private readonly api = inject(CrmCustomerApiService);
  private readonly overlay = inject(CrmSessionOverlayService);

  loading = false;
  error: string | null = null;
  customer: CustomerDetail | null = null;
  private baseCustomer: CustomerDetail | null = null;
  commentText = '';
  commentError: string | null = null;

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['open']?.currentValue && this.customerId) {
      this.loadDetail(this.customerId);
    }
    if (!this.open) {
      this.resetForm();
    }
  }

  close(): void {
    this.closed.emit();
  }

  onBackdropClick(event: MouseEvent): void {
    if ((event.target as HTMLElement).classList.contains('crm-modal__backdrop')) {
      this.close();
    }
  }

  onWarmChange(value: WarmStatus): void {
    if (!this.baseCustomer) {
      return;
    }
    this.overlay.setWarmStatus(this.baseCustomer.id, value);
    this.refreshCustomerView();
    this.customerUpdated.emit();
    this.toast.emit(this.i18n.t('warmUpdated'));
  }

  addComment(): void {
    const trimmed = this.commentText.trim();
    if (!trimmed) {
      this.commentError = this.i18n.t('commentEmpty');
      return;
    }
    if (trimmed.length > 500) {
      this.commentError = this.i18n.t('commentTooLong');
      return;
    }
    if (!this.baseCustomer) {
      return;
    }
    const author = this.i18n.locale() === 'pt-BR' ? 'Vendedor demo' : 'Demo seller';
    this.overlay.addComment(this.baseCustomer.id, trimmed, author);
    this.refreshCustomerView();
    this.commentText = '';
    this.commentError = null;
    this.customerUpdated.emit();
  }

  private loadDetail(id: string): void {
    this.loading = true;
    this.error = null;
    this.customer = null;
    this.api.getCustomer(id).subscribe({
      next: (detail) => {
        this.baseCustomer = detail;
        this.refreshCustomerView();
        this.loading = false;
      },
      error: (err) => {
        this.loading = false;
        if (err.status === 404) {
          this.error = this.i18n.t('customerNotFound');
        } else {
          this.error = this.i18n.t('errorLoad');
        }
      },
    });
  }

  private refreshCustomerView(): void {
    this.customer = this.baseCustomer ? this.overlay.applyToDetail(this.baseCustomer) : null;
  }

  private resetForm(): void {
    this.commentText = '';
    this.commentError = null;
    this.error = null;
    this.customer = null;
    this.baseCustomer = null;
  }
}
