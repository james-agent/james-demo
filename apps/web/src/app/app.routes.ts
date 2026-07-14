import { Routes } from '@angular/router';
import { CrmShellComponent } from './layout/crm-shell/crm-shell.component';
import { DashboardWelcomeComponent } from './features/dashboard/dashboard-welcome.component';

export const routes: Routes = [
  {
    path: 'inception_no_prod',
    loadChildren: () =>
      import('./james_inception/inception.routes').then((m) => m.inceptionRoutes),
  },
  {
    path: '',
    component: CrmShellComponent,
    children: [
      { path: '', component: DashboardWelcomeComponent },
      {
        path: 'leads',
        loadComponent: () =>
          import('./james_inception/crm/lead-list.component').then(
            (m) => m.LeadListComponent,
          ),
      },
      {
        path: 'accounts',
        loadComponent: () =>
          import('./james_inception/crm/customer-list.component').then(
            (m) => m.CustomerListComponent,
          ),
      },
    ],
  },
];
