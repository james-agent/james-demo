import { Routes } from '@angular/router';

import { CustomerListComponent } from './crm/customer-list.component';
import { OpportunityDetailInceptionComponent } from './crm/opportunity-detail-inception.component';
import { OpportunityFormInceptionComponent } from './crm/opportunity-form-inception.component';
import { OpportunityShellComponent } from './crm/opportunity-shell.component';
import { InceptionShellComponent } from './inception-shell.component';

export const inceptionRoutes: Routes = [
  {
    path: '',
    component: InceptionShellComponent,
    children: [
      {
        path: 'crm/clientes',
        component: CustomerListComponent,
      },
      {
        path: 'crm/opportunities/new',
        component: OpportunityFormInceptionComponent,
      },
      {
        path: 'crm/opportunities/:id/edit',
        component: OpportunityFormInceptionComponent,
      },
      {
        path: 'crm/opportunities/:id',
        component: OpportunityDetailInceptionComponent,
      },
      {
        path: 'crm/opportunities',
        component: OpportunityShellComponent,
      },
    ],
  },
];
