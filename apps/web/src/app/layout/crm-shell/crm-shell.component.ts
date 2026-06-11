import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { SidebarComponent } from '../sidebar/sidebar.component';

@Component({
  selector: 'app-crm-shell',
  standalone: true,
  imports: [RouterOutlet, SidebarComponent],
  templateUrl: './crm-shell.component.html',
  styleUrl: './crm-shell.component.css',
})
export class CrmShellComponent {
  sidebarOpen = false;

  toggleSidebar(): void {
    this.sidebarOpen = !this.sidebarOpen;
  }

  closeSidebar(): void {
    this.sidebarOpen = false;
  }
}
