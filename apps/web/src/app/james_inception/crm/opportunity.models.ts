export type OpportunityStage =
  | 'qualificacao'
  | 'proposta'
  | 'negociacao'
  | 'fechado_ganho'
  | 'fechado_perdido';

export const OPPORTUNITY_STAGES: OpportunityStage[] = [
  'qualificacao',
  'proposta',
  'negociacao',
  'fechado_ganho',
  'fechado_perdido',
];

export const STAGE_LABELS: Record<OpportunityStage, string> = {
  qualificacao: 'Qualificação',
  proposta: 'Proposta',
  negociacao: 'Negociação',
  fechado_ganho: 'Fechado ganho',
  fechado_perdido: 'Fechado perdido',
};

export type MockRole = 'vendedor' | 'gerente';
export type ViewMode = 'table' | 'kanban';

export interface ProductLine {
  id: string;
  item: string;
  quantity: number;
  unitPrice: number;
}

export interface Opportunity {
  id: string;
  name: string;
  account: string;
  value: number;
  stage: OpportunityStage;
  probability: number;
  closeDate: string;
  owner: string;
  ownerTeam: string;
  description: string;
  nextStep: string;
  productLines: ProductLine[];
}

export function lineTotal(line: ProductLine): number {
  return line.quantity * line.unitPrice;
}

export function computeLineTotal(line: ProductLine): number {
  return lineTotal(line);
}

export function productLinesTotal(lines: ProductLine[]): number {
  return lines.reduce((sum, line) => sum + lineTotal(line), 0);
}
