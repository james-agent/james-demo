import { Component } from '@angular/core';

@Component({
  selector: 'app-dashboard-welcome',
  standalone: true,
  templateUrl: './dashboard-welcome.component.html',
  styleUrl: './dashboard-welcome.component.css',
})
export class DashboardWelcomeComponent {
  readonly headline = 'Welcome back';
  readonly subtext = 'Your CRM dashboard is ready';
}
