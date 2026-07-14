import { Injectable, signal } from '@angular/core';

import { CrmLocale } from './crm.models';

type MessageKey =
  | 'title'
  | 'filterName'
  | 'filterEmail'
  | 'filterFreeSearch'
  | 'clearFilters'
  | 'viewDetail'
  | 'loading'
  | 'retry'
  | 'emptyNoData'
  | 'emptyNoMatch'
  | 'errorLoad'
  | 'demoNote'
  | 'pageOf'
  | 'totalRecords'
  | 'colName'
  | 'colEmail'
  | 'colCompany'
  | 'colCountry'
  | 'colState'
  | 'colStatus'
  | 'colWarm'
  | 'colInclusion'
  | 'colLastComm'
  | 'colPhone'
  | 'colSegment'
  | 'colOwner'
  | 'colLeadSource'
  | 'colActions'
  | 'warmHot'
  | 'warmWarm'
  | 'detailStub'
  | 'localeLabel';

const MESSAGES: Record<CrmLocale, Record<MessageKey, string>> = {
  'en-US': {
    title: 'Leads',
    filterName: 'Name',
    filterEmail: 'Email',
    filterFreeSearch: 'Free search',
    clearFilters: 'Clear filters',
    viewDetail: 'View detail',
    loading: 'Loading leads…',
    retry: 'Try again',
    emptyNoData: 'No leads available.',
    emptyNoMatch: 'No leads found matching your filters.',
    errorLoad: 'Could not load leads. Please try again.',
    demoNote: 'Lead list is mock-only in this demo — no API or persistence.',
    pageOf: 'Page {page} of {total}',
    totalRecords: '{count} records',
    colName: 'Name',
    colEmail: 'Email',
    colCompany: 'Company',
    colCountry: 'Country',
    colState: 'State',
    colStatus: 'Status',
    colWarm: 'Status warm',
    colInclusion: 'Inclusion date',
    colLastComm: 'Last communication date',
    colPhone: 'Phone',
    colSegment: 'Segment',
    colOwner: 'Account owner',
    colLeadSource: 'Lead source',
    colActions: 'Actions',
    warmHot: 'Hot',
    warmWarm: 'Warm',
    detailStub: 'Lead detail is not available in this mock list.',
    localeLabel: 'Language',
  },
  'pt-BR': {
    title: 'Leads',
    filterName: 'Nome',
    filterEmail: 'E-mail',
    filterFreeSearch: 'Busca livre',
    clearFilters: 'Limpar filtros',
    viewDetail: 'Ver detalhe',
    loading: 'Carregando leads…',
    retry: 'Tentar novamente',
    emptyNoData: 'Nenhum lead disponível.',
    emptyNoMatch: 'Nenhum lead encontrado com os filtros informados.',
    errorLoad: 'Não foi possível carregar os leads. Tente novamente.',
    demoNote: 'A lista de leads é apenas mock nesta demo — sem API ou persistência.',
    pageOf: 'Página {page} de {total}',
    totalRecords: '{count} registros',
    colName: 'Nome',
    colEmail: 'E-mail',
    colCompany: 'Empresa',
    colCountry: 'País',
    colState: 'Estado',
    colStatus: 'Status',
    colWarm: 'Status warm',
    colInclusion: 'Data de inclusão',
    colLastComm: 'Data da última comunicação',
    colPhone: 'Telefone',
    colSegment: 'Segmento',
    colOwner: 'Responsável',
    colLeadSource: 'Origem do lead',
    colActions: 'Ações',
    warmHot: 'Quente',
    warmWarm: 'Morno',
    detailStub: 'Detalhe do lead não está disponível nesta lista mock.',
    localeLabel: 'Idioma',
  },
};

@Injectable({ providedIn: 'root' })
export class LeadI18nService {
  readonly locale = signal<CrmLocale>('en-US');

  t(key: MessageKey, params?: Record<string, string | number>): string {
    let text = MESSAGES[this.locale()][key];
    if (params) {
      for (const [name, value] of Object.entries(params)) {
        text = text.replace(`{${name}}`, String(value));
      }
    }
    return text;
  }

  formatDate(iso: string | null): string {
    if (!iso) {
      return '—';
    }
    const date = new Date(iso);
    const loc = this.locale() === 'pt-BR' ? 'pt-BR' : 'en-US';
    return new Intl.DateTimeFormat(loc, {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }).format(date);
  }

  warmLabel(status: 'Hot' | 'Warm'): string {
    return status === 'Hot' ? this.t('warmHot') : this.t('warmWarm');
  }

  setLocale(locale: CrmLocale): void {
    this.locale.set(locale);
  }
}
