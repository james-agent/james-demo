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
  | 'modalTitle'
  | 'close'
  | 'comments'
  | 'noComments'
  | 'addComment'
  | 'commentPlaceholder'
  | 'commentEmpty'
  | 'commentTooLong'
  | 'newBadge'
  | 'warmUpdated'
  | 'customerNotFound'
  | 'localeLabel';

const MESSAGES: Record<CrmLocale, Record<MessageKey, string>> = {
  'en-US': {
    title: 'Customers',
    filterName: 'Name',
    filterEmail: 'Email',
    filterFreeSearch: 'Free search',
    clearFilters: 'Clear filters',
    viewDetail: 'View detail',
    loading: 'Loading customers…',
    retry: 'Try again',
    emptyNoData: 'No customers available.',
    emptyNoMatch: 'No customers found matching your filters.',
    errorLoad: 'Could not load customers. Please try again.',
    demoNote:
      'Comments and warm status changes are temporary in this demo and reset after reload.',
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
    modalTitle: 'Customer detail',
    close: 'Close',
    comments: 'Comments',
    noComments: 'No comments yet',
    addComment: 'Add',
    commentPlaceholder: 'Write a comment (max 500 characters)',
    commentEmpty: 'Comment cannot be empty.',
    commentTooLong: 'Comment must be at most 500 characters.',
    newBadge: 'New',
    warmUpdated: 'Warm status updated',
    customerNotFound: 'Customer not found',
    localeLabel: 'Language',
  },
  'pt-BR': {
    title: 'Clientes',
    filterName: 'Nome',
    filterEmail: 'E-mail',
    filterFreeSearch: 'Busca livre',
    clearFilters: 'Limpar filtros',
    viewDetail: 'Ver detalhe',
    loading: 'Carregando clientes…',
    retry: 'Tentar novamente',
    emptyNoData: 'Nenhum cliente disponível.',
    emptyNoMatch: 'Nenhum cliente encontrado com os filtros informados.',
    errorLoad: 'Não foi possível carregar os clientes. Tente novamente.',
    demoNote:
      'Comentários e alterações de status warm são temporários nesta demo e revertem após recarregar.',
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
    modalTitle: 'Detalhe do cliente',
    close: 'Fechar',
    comments: 'Comentários',
    noComments: 'Nenhum comentário ainda',
    addComment: 'Adicionar',
    commentPlaceholder: 'Escreva um comentário (máx. 500 caracteres)',
    commentEmpty: 'O comentário não pode estar vazio.',
    commentTooLong: 'O comentário deve ter no máximo 500 caracteres.',
    newBadge: 'Novo',
    warmUpdated: 'Status warm atualizado',
    customerNotFound: 'Cliente não encontrado',
    localeLabel: 'Idioma',
  },
};

@Injectable({ providedIn: 'root' })
export class CrmI18nService {
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
