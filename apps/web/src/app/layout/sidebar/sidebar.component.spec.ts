import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { SidebarComponent } from './sidebar.component';
import { NAV_MENU_ITEMS } from './nav-menu.config';

describe('SidebarComponent', () => {
  let fixture: ComponentFixture<SidebarComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SidebarComponent],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(SidebarComponent);
    fixture.detectChanges();
  });

  it('renders eight menu labels in order', () => {
    const labels = Array.from(
      fixture.nativeElement.querySelectorAll('.sidebar-nav__link') as NodeListOf<HTMLElement>,
    ).map((el) => el.textContent?.trim());

    expect(labels).toEqual(NAV_MENU_ITEMS.map((item) => item.label));
  });

  it('links Leads to the lead list route', () => {
    const leadsLink = Array.from(
      fixture.nativeElement.querySelectorAll('.sidebar-nav__link') as NodeListOf<HTMLAnchorElement>,
    ).find((el) => el.textContent?.trim() === 'Leads');

    expect(leadsLink?.getAttribute('href')).toBe('/leads');
  });

  it('links Accounts to the customer list route', () => {
    const accountsLink = Array.from(
      fixture.nativeElement.querySelectorAll('.sidebar-nav__link') as NodeListOf<HTMLAnchorElement>,
    ).find((el) => el.textContent?.trim() === 'Accounts');

    expect(accountsLink?.getAttribute('href')).toBe('/accounts');
  });

  it('links Oportunidades to inception opportunities route', () => {
    const opportunitiesLink = Array.from(
      fixture.nativeElement.querySelectorAll('.sidebar-nav__link') as NodeListOf<HTMLAnchorElement>,
    ).find((el) => el.textContent?.trim() === 'Oportunidades');

    expect(opportunitiesLink?.getAttribute('href')).toBe('/inception_no_prod/crm/opportunities');
  });

  it('applies disabled styling to placeholder items', () => {
    const disabledLinks = fixture.nativeElement.querySelectorAll(
      '.sidebar-nav__link--disabled',
    );

    expect(disabledLinks.length).toBe(4);
  });

  it('shows Coming soon tooltip when a placeholder item is clicked', () => {
    const contactsButton = Array.from(
      fixture.nativeElement.querySelectorAll('.sidebar-nav__link') as NodeListOf<HTMLElement>,
    ).find((el) => el.textContent?.trim() === 'Contacts') as HTMLButtonElement;

    contactsButton.click();
    fixture.detectChanges();

    const tooltip = contactsButton.querySelector('.coming-soon-tooltip');
    expect(tooltip?.textContent?.trim()).toBe('Coming soon');
  });
});
