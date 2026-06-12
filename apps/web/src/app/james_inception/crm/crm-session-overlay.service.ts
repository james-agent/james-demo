import { Injectable } from '@angular/core';

import { CustomerComment, CustomerDetail, CustomerSummary, WarmStatus } from './crm.models';

interface SessionOverlay {
  warmStatus?: WarmStatus;
  lastCommunicationDate?: string;
  sessionComments: CustomerComment[];
}

@Injectable({ providedIn: 'root' })
export class CrmSessionOverlayService {
  private readonly overlays = new Map<string, SessionOverlay>();

  applyToSummary(customer: CustomerSummary): CustomerSummary {
    const overlay = this.overlays.get(customer.id);
    if (!overlay) {
      return customer;
    }
    return {
      ...customer,
      warmStatus: overlay.warmStatus ?? customer.warmStatus,
      lastCommunicationDate: overlay.lastCommunicationDate ?? customer.lastCommunicationDate,
    };
  }

  applyToDetail(customer: CustomerDetail): CustomerDetail {
    const overlay = this.overlays.get(customer.id);
    if (!overlay) {
      return customer;
    }
    const apiComments = customer.comments.filter((c) => !c.isSession);
    const mergedComments = [...overlay.sessionComments, ...apiComments].sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
    );
    return {
      ...customer,
      warmStatus: overlay.warmStatus ?? customer.warmStatus,
      lastCommunicationDate: overlay.lastCommunicationDate ?? customer.lastCommunicationDate,
      comments: mergedComments,
    };
  }

  addComment(customerId: string, text: string, author: string): void {
    const overlay = this.getOrCreate(customerId);
    const now = new Date().toISOString();
    overlay.sessionComments.unshift({
      id: `session-${Date.now()}`,
      text,
      author,
      createdAt: now,
      isSession: true,
    });
    overlay.lastCommunicationDate = now;
  }

  setWarmStatus(customerId: string, warmStatus: WarmStatus): void {
    const overlay = this.getOrCreate(customerId);
    overlay.warmStatus = warmStatus;
  }

  private getOrCreate(customerId: string): SessionOverlay {
    let overlay = this.overlays.get(customerId);
    if (!overlay) {
      overlay = { sessionComments: [] };
      this.overlays.set(customerId, overlay);
    }
    return overlay;
  }
}
