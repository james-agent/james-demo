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
    children: [{ path: '', component: DashboardWelcomeComponent }],
  },
];
