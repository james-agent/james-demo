import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SidebarComponent } from './sidebar.component';
import { NAV_MENU_ITEMS } from './nav-menu.config';

describe('SidebarComponent', () => {
  let fixture: ComponentFixture<SidebarComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SidebarComponent],
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

  it('marks Dashboard as active', () => {
    const activeLink = fixture.nativeElement.querySelector(
      '.sidebar-nav__link--active',
    ) as HTMLElement;

    expect(activeLink?.textContent?.trim()).toBe('Dashboard');
  });

  it('applies disabled styling to placeholder items', () => {
    const disabledLinks = fixture.nativeElement.querySelectorAll(
      '.sidebar-nav__link--disabled',
    );

    expect(disabledLinks.length).toBe(7);
  });

  it('shows Coming soon tooltip when a placeholder item is clicked', () => {
    const leadsButton = fixture.nativeElement.querySelectorAll(
      '.sidebar-nav__link',
    )[1] as HTMLButtonElement;

    leadsButton.click();
    fixture.detectChanges();

    const tooltip = leadsButton.querySelector('.coming-soon-tooltip');
    expect(tooltip?.textContent?.trim()).toBe('Coming soon');
  });
});
