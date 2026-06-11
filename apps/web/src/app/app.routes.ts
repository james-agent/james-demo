import { Routes } from '@angular/router';
import { CrmShellComponent } from './layout/crm-shell/crm-shell.component';
import { DashboardWelcomeComponent } from './features/dashboard/dashboard-welcome.component';

export const routes: Routes = [
  {
    path: '',
    component: CrmShellComponent,
    children: [{ path: '', component: DashboardWelcomeComponent }],
  },
];
