export interface NavMenuItem {
  id: string;
  label: string;
  route?: string;
  disabled: boolean;
}

export const NAV_MENU_ITEMS: NavMenuItem[] = [
  { id: 'dashboard', label: 'Dashboard', route: '/', disabled: false },
  { id: 'leads', label: 'Leads', disabled: true },
  { id: 'accounts', label: 'Accounts', route: '/accounts', disabled: false },
  { id: 'contacts', label: 'Contacts', disabled: true },
  { id: 'opportunities', label: 'Opportunities', disabled: true },
  { id: 'activities', label: 'Activities', disabled: true },
  { id: 'reports', label: 'Reports', disabled: true },
  { id: 'settings', label: 'Settings', disabled: true },
];
