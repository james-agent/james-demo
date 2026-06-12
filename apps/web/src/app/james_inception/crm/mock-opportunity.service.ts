import { Injectable, signal } from '@angular/core';

import {
  MockRole,
  Opportunity,
  OpportunityStage,
  ProductLine,
  ViewMode,
  productLinesTotal,
} from './opportunity.models';

const SELLERS = ['Ana Silva', 'Bruno Costa', 'Carla Mendes'];
const TEAMS = ['Norte', 'Sul', 'Enterprise'];

function line(id: string, item: string, quantity: number, unitPrice: number): ProductLine {
  return { id, item, quantity, unitPrice };
}

function seedOpportunities(): Opportunity[] {
  return [
    {
      id: 'opp-001',
      name: 'Expansão ERP TechCorp',
      account: 'TechCorp Ltda',
      value: 185000,
      stage: 'qualificacao',
      probability: 20,
      closeDate: '2026-08-15',
      owner: 'Ana Silva',
      ownerTeam: 'Norte',
      description: 'Renovação e expansão de licenças ERP.',
      nextStep: 'Agendar demo técnica',
      productLines: [
        line('pl-001', 'Licença ERP Premium', 50, 2500),
        line('pl-002', 'Implantação', 1, 35000),
      ],
    },
    {
      id: 'opp-002',
      name: 'Pacote Cloud FinBank',
      account: 'FinBank',
      value: 92000,
      stage: 'proposta',
      probability: 45,
      closeDate: '2026-07-01',
      owner: 'Bruno Costa',
      ownerTeam: 'Sul',
      description: 'Migração parcial para cloud privada.',
      nextStep: 'Enviar proposta revisada',
      productLines: [line('pl-003', 'Cloud Node', 12, 4500), line('pl-004', 'Suporte 24x7', 12, 2500)],
    },
    {
      id: 'opp-003',
      name: 'CRM RetailMax',
      account: 'RetailMax',
      value: 64000,
      stage: 'negociacao',
      probability: 70,
      closeDate: '2026-06-30',
      owner: 'Ana Silva',
      ownerTeam: 'Norte',
      description: 'CRM para 120 lojas.',
      nextStep: 'Negociar desconto volume',
      productLines: [line('pl-005', 'Licença CRM', 120, 400)],
    },
    {
      id: 'opp-004',
      name: 'BI Analytics HealthPlus',
      account: 'HealthPlus',
      value: 128000,
      stage: 'qualificacao',
      probability: 25,
      closeDate: '2026-09-10',
      owner: 'Carla Mendes',
      ownerTeam: 'Enterprise',
      description: 'Dashboard executivo e integração FHIR.',
      nextStep: 'Workshop com TI',
      productLines: [line('pl-006', 'BI Suite', 1, 98000), line('pl-007', 'Treinamento', 5, 6000)],
    },
    {
      id: 'opp-005',
      name: 'Segurança LogiTrans',
      account: 'LogiTrans',
      value: 45000,
      stage: 'proposta',
      probability: 50,
      closeDate: '2026-07-20',
      owner: 'Bruno Costa',
      ownerTeam: 'Sul',
      description: 'Firewall e SOC gerenciado.',
      nextStep: 'Validar arquitetura',
      productLines: [line('pl-008', 'Firewall HA', 2, 12000), line('pl-009', 'SOC mensal', 12, 1750)],
    },
    {
      id: 'opp-006',
      name: 'E-commerce AgroVerde',
      account: 'AgroVerde',
      value: 78000,
      stage: 'negociacao',
      probability: 65,
      closeDate: '2026-06-25',
      owner: 'Carla Mendes',
      ownerTeam: 'Enterprise',
      description: 'Plataforma B2B com catálogo dinâmico.',
      nextStep: 'Aprovar SLA',
      productLines: [line('pl-010', 'Plataforma B2B', 1, 55000), line('pl-011', 'Customização', 1, 23000)],
    },
    {
      id: 'opp-007',
      name: 'Mobile App EduFuture',
      account: 'EduFuture',
      value: 36000,
      stage: 'fechado_ganho',
      probability: 100,
      closeDate: '2026-05-15',
      owner: 'Ana Silva',
      ownerTeam: 'Norte',
      description: 'App aluno + portal responsivo.',
      nextStep: 'Kick-off implantação',
      productLines: [line('pl-012', 'App Mobile', 1, 28000), line('pl-013', 'Portal Web', 1, 8000)],
    },
    {
      id: 'opp-008',
      name: 'Data Lake MetalWorks',
      account: 'MetalWorks',
      value: 210000,
      stage: 'qualificacao',
      probability: 15,
      closeDate: '2026-10-01',
      owner: 'Bruno Costa',
      ownerTeam: 'Sul',
      description: 'Lakehouse para linha de produção.',
      nextStep: 'POC ingestão IoT',
      productLines: [line('pl-014', 'Data Lake', 1, 150000), line('pl-015', 'Conectores IoT', 20, 3000)],
    },
    {
      id: 'opp-009',
      name: 'VoIP CallCenter SoftPhone',
      account: 'SoftPhone',
      value: 52000,
      stage: 'fechado_perdido',
      probability: 0,
      closeDate: '2026-04-01',
      owner: 'Carla Mendes',
      ownerTeam: 'Enterprise',
      description: 'Substituição de PABX legado.',
      nextStep: 'Arquivar',
      productLines: [line('pl-016', 'Licenças VoIP', 200, 200)],
    },
    {
      id: 'opp-010',
      name: 'Automação RH PeopleFirst',
      account: 'PeopleFirst',
      value: 41000,
      stage: 'proposta',
      probability: 40,
      closeDate: '2026-08-05',
      owner: 'Ana Silva',
      ownerTeam: 'Norte',
      description: 'RPA para admissão e folha.',
      nextStep: 'Demo RPA',
      productLines: [line('pl-017', 'Bot admissão', 3, 8000), line('pl-018', 'Bot folha', 2, 8500)],
    },
    {
      id: 'opp-011',
      name: 'Backup DR Construtora Alfa',
      account: 'Construtora Alfa',
      value: 67000,
      stage: 'negociacao',
      probability: 75,
      closeDate: '2026-06-18',
      owner: 'Bruno Costa',
      ownerTeam: 'Sul',
      description: 'DR site secundário.',
      nextStep: 'Teste failover',
      productLines: [line('pl-019', 'Storage DR', 1, 45000), line('pl-020', 'Replicação', 12, 1750)],
    },
    {
      id: 'opp-012',
      name: 'Marketing Hub VivaMais',
      account: 'VivaMais',
      value: 29500,
      stage: 'qualificacao',
      probability: 30,
      closeDate: '2026-09-22',
      owner: 'Carla Mendes',
      ownerTeam: 'Enterprise',
      description: 'Automação de campanhas.',
      nextStep: 'Mapear integrações',
      productLines: [line('pl-021', 'Marketing Hub', 1, 22000), line('pl-022', 'Consultoria', 5, 1500)],
    },
  ];
}

@Injectable({ providedIn: 'root' })
export class MockOpportunityService {
  private readonly opportunities = signal<Opportunity[]>(seedOpportunities());
  private readonly role = signal<MockRole>('vendedor');
  private readonly viewMode = signal<ViewMode>('table');
  private readonly sellerFilter = signal<string>('');
  private readonly teamFilter = signal<string>('');

  readonly roleState = this.role.asReadonly();
  readonly viewModeState = this.viewMode.asReadonly();
  readonly sellerFilterState = this.sellerFilter.asReadonly();
  readonly teamFilterState = this.teamFilter.asReadonly();

  readonly sellers = SELLERS;
  readonly teams = TEAMS;
  readonly simulatedSeller = 'Ana Silva';

  setRole(role: MockRole): void {
    this.role.set(role);
    this.viewMode.set(role === 'vendedor' ? 'table' : 'kanban');
    if (role === 'vendedor') {
      this.sellerFilter.set('');
      this.teamFilter.set('');
    }
  }

  setViewMode(mode: ViewMode): void {
    this.viewMode.set(mode);
  }

  setSellerFilter(seller: string): void {
    this.sellerFilter.set(seller);
  }

  setTeamFilter(team: string): void {
    this.teamFilter.set(team);
  }

  getFiltered(): Opportunity[] {
    let list = [...this.opportunities()];
    const role = this.role();

    if (role === 'vendedor') {
      list = list.filter((o) => o.owner === this.simulatedSeller);
    } else {
      const seller = this.sellerFilter();
      const team = this.teamFilter();
      if (seller) {
        list = list.filter((o) => o.owner === seller);
      }
      if (team) {
        list = list.filter((o) => o.ownerTeam === team);
      }
    }

    return list;
  }

  getById(id: string): Opportunity | undefined {
    return this.opportunities().find((o) => o.id === id);
  }

  updateStage(id: string, stage: OpportunityStage): boolean {
    const idx = this.opportunities().findIndex((o) => o.id === id);
    if (idx === -1) {
      return false;
    }
    const updated = { ...this.opportunities()[idx], stage };
    this.opportunities.update((list) => {
      const copy = [...list];
      copy[idx] = updated;
      return copy;
    });
    return true;
  }

  create(payload: Omit<Opportunity, 'id'>): Opportunity {
    const id = `opp-${Date.now()}`;
    const opportunity: Opportunity = { ...payload, id };
    this.opportunities.update((list) => [...list, opportunity]);
    return opportunity;
  }

  update(id: string, payload: Partial<Opportunity>): Opportunity | null {
    const idx = this.opportunities().findIndex((o) => o.id === id);
    if (idx === -1) {
      return null;
    }
    const merged = { ...this.opportunities()[idx], ...payload, id };
    this.opportunities.update((list) => {
      const copy = [...list];
      copy[idx] = merged;
      return copy;
    });
    return merged;
  }

  buildPayloadFromForm(
    form: {
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
    },
  ): Omit<Opportunity, 'id'> {
    const value = productLinesTotal(form.productLines);
    return {
      name: form.name.trim(),
      account: form.account.trim(),
      value,
      stage: form.stage,
      probability: form.probability,
      closeDate: form.closeDate,
      owner: form.owner,
      ownerTeam: form.ownerTeam,
      description: form.description.trim(),
      nextStep: form.nextStep.trim(),
      productLines: form.productLines.map((pl) => ({ ...pl })),
    };
  }
}
