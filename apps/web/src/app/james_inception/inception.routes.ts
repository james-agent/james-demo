import { Routes } from '@angular/router';

import { CustomerListComponent } from './crm/customer-list.component';
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
    ],
  },
];
