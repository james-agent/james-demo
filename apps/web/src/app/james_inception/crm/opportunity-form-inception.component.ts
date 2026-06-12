/**
 * @JAMES-INCEPTION-CARD
 * @card-id: JAMESD-6
 * @description: CRM opportunity MOCK create/edit form with product lines and client-side validation.
 * MOCK only — not production; safe for another agent to use as a migration anchor.
 */
import { Component, inject, OnInit } from '@angular/core';
import {
  FormArray,
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import {
  OPPORTUNITY_STAGES,
  OpportunityStage,
  ProductLine,
  STAGE_LABELS,
  computeLineTotal,
  productLinesTotal,
} from './opportunity.models';
import { MockOpportunityService } from './mock-opportunity.service';

@Component({
  selector: 'app-opportunity-form-inception',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './opportunity-form-inception.component.html',
  styleUrl: './opportunity-form-inception.component.css',
})
export class OpportunityFormInceptionComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly mock = inject(MockOpportunityService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly stages = OPPORTUNITY_STAGES;
  readonly sellers = this.mock.sellers;
  readonly teams = this.mock.teams;

  form!: FormGroup;
  isEdit = false;
  opportunityId: string | null = null;
  toastMessage: string | null = null;
  private toastTimer: ReturnType<typeof setTimeout> | null = null;

  ngOnInit(): void {
    this.form = this.fb.group({
      name: ['', Validators.required],
      account: [''],
      stage: ['qualificacao' as OpportunityStage, Validators.required],
      probability: [20, [Validators.required, Validators.min(0), Validators.max(100)]],
      closeDate: [''],
      owner: [this.mock.simulatedSeller, Validators.required],
      ownerTeam: ['Norte', Validators.required],
      description: [''],
      nextStep: [''],
      productLines: this.fb.array([]),
    });

    const id = this.route.snapshot.paramMap.get('id');
    const isEditPath = this.route.snapshot.url.some((s) => s.path === 'edit');

    if (id && isEditPath) {
      const existing = this.mock.getById(id);
      if (!existing) {
        this.redirectWithError();
        return;
      }
      this.isEdit = true;
      this.opportunityId = id;
      this.populateForm(existing);
    } else if (id) {
      this.redirectWithError();
    } else {
      this.addProductLine();
    }
  }

  get productLines(): FormArray {
    return this.form.get('productLines') as FormArray;
  }

  stageLabel(stage: OpportunityStage): string {
    return STAGE_LABELS[stage];
  }

  addProductLine(line?: ProductLine): void {
    this.productLines.push(
      this.fb.group({
        id: [line?.id ?? `pl-new-${Date.now()}`],
        item: [line?.item ?? '', Validators.required],
        quantity: [line?.quantity ?? 1, [Validators.required, Validators.min(1)]],
        unitPrice: [line?.unitPrice ?? 0, [Validators.required, Validators.min(0)]],
      }),
    );
  }

  removeProductLine(index: number): void {
    if (this.productLines.length > 1) {
      this.productLines.removeAt(index);
    }
  }

  lineTotalAt(index: number): number {
    const group = this.productLines.at(index);
    return computeLineTotal({
      id: group.get('id')?.value,
      item: group.get('item')?.value,
      quantity: Number(group.get('quantity')?.value) || 0,
      unitPrice: Number(group.get('unitPrice')?.value) || 0,
    });
  }

  grandTotal(): number {
    const lines: ProductLine[] = this.productLines.controls.map((ctrl) => ({
      id: ctrl.get('id')?.value,
      item: ctrl.get('item')?.value,
      quantity: Number(ctrl.get('quantity')?.value) || 0,
      unitPrice: Number(ctrl.get('unitPrice')?.value) || 0,
    }));
    return productLinesTotal(lines);
  }

  formatCurrency(value: number): string {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
  }

  save(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.showToast('Corrija os campos obrigatórios');
      return;
    }

    const raw = this.form.getRawValue();
    const productLines: ProductLine[] = raw.productLines.map((pl: ProductLine) => ({
      id: pl.id,
      item: pl.item,
      quantity: Number(pl.quantity),
      unitPrice: Number(pl.unitPrice),
    }));

    const payload = this.mock.buildPayloadFromForm({
      name: raw.name,
      account: raw.account,
      stage: raw.stage,
      probability: Number(raw.probability),
      closeDate: raw.closeDate,
      owner: raw.owner,
      ownerTeam: raw.ownerTeam,
      description: raw.description,
      nextStep: raw.nextStep,
      productLines,
    });

    if (this.isEdit && this.opportunityId) {
      const updated = this.mock.update(this.opportunityId, payload);
      if (!updated) {
        this.redirectWithError();
        return;
      }
      this.showToast('Oportunidade atualizada');
      setTimeout(() => {
        this.router.navigate(['/inception_no_prod/crm/opportunities', this.opportunityId]);
      }, 600);
    } else {
      const created = this.mock.create(payload);
      this.showToast('Oportunidade criada');
      setTimeout(() => {
        this.router.navigate(['/inception_no_prod/crm/opportunities']);
      }, 600);
    }
  }

  cancel(): void {
    if (this.isEdit && this.opportunityId) {
      this.router.navigate(['/inception_no_prod/crm/opportunities', this.opportunityId]);
    } else {
      this.router.navigate(['/inception_no_prod/crm/opportunities']);
    }
  }

  private populateForm(existing: {
    name: string;
    account: string;
    stage: OpportunityStage;
    probability: number;
    closeDate: string;
    owner: string;
    ownerTeam: string;
    description: string;
    nextStep: string;
    productLines: ProductLine[];
  }): void {
    this.form.patchValue({
      name: existing.name,
      account: existing.account,
      stage: existing.stage,
      probability: existing.probability,
      closeDate: existing.closeDate,
      owner: existing.owner,
      ownerTeam: existing.ownerTeam,
      description: existing.description,
      nextStep: existing.nextStep,
    });
    this.productLines.clear();
    if (existing.productLines.length === 0) {
      this.addProductLine();
    } else {
      existing.productLines.forEach((line) => this.addProductLine(line));
    }
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
