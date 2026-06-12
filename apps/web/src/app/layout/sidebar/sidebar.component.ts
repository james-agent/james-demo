import { Component } from '@angular/core';
import { NAV_MENU_ITEMS, NavMenuItem } from './nav-menu.config';
import { ComingSoonDirective } from '../../shared/coming-soon/coming-soon.directive';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [ComingSoonDirective],
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.css',
})
export class SidebarComponent {
  readonly menuItems: NavMenuItem[] = NAV_MENU_ITEMS;

  onItemClick(item: NavMenuItem, event: Event): void {
    if (item.disabled) {
      event.preventDefault();
      event.stopPropagation();
    }
  }
}
