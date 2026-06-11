export interface NavMenuItem {
  id: string;
  label: string;
  disabled: boolean;
  active: boolean;
}

export const NAV_MENU_ITEMS: NavMenuItem[] = [
  { id: 'dashboard', label: 'Dashboard', disabled: false, active: true },
  { id: 'leads', label: 'Leads', disabled: true, active: false },
  { id: 'accounts', label: 'Accounts', disabled: true, active: false },
  { id: 'contacts', label: 'Contacts', disabled: true, active: false },
  { id: 'opportunities', label: 'Opportunities', disabled: true, active: false },
  { id: 'activities', label: 'Activities', disabled: true, active: false },
  { id: 'reports', label: 'Reports', disabled: true, active: false },
  { id: 'settings', label: 'Settings', disabled: true, active: false },
];
