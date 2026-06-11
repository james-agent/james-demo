import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { CrmShellComponent } from './crm-shell.component';
import { DashboardWelcomeComponent } from '../../features/dashboard/dashboard-welcome.component';

describe('CrmShellComponent', () => {
  let fixture: ComponentFixture<CrmShellComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CrmShellComponent],
      providers: [
        provideRouter([
          {
            path: '',
            component: CrmShellComponent,
            children: [{ path: '', component: DashboardWelcomeComponent }],
          },
        ]),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(CrmShellComponent);
    fixture.detectChanges();
  });

  it('toggles sidebar open state when hamburger is clicked', () => {
    expect(fixture.componentInstance.sidebarOpen).toBeFalse();

    const hamburger = fixture.nativeElement.querySelector(
      '.crm-shell__hamburger',
    ) as HTMLButtonElement;
    hamburger.click();
    fixture.detectChanges();

    expect(fixture.componentInstance.sidebarOpen).toBeTrue();
    expect(
      fixture.nativeElement.querySelector('.crm-shell')?.classList.contains('crm-shell--sidebar-open'),
    ).toBeTrue();
  });

  it('closes sidebar when backdrop is clicked', () => {
    fixture.componentInstance.sidebarOpen = true;
    fixture.detectChanges();

    const backdrop = fixture.nativeElement.querySelector(
      '.crm-shell__backdrop',
    ) as HTMLButtonElement;
    backdrop.click();
    fixture.detectChanges();

    expect(fixture.componentInstance.sidebarOpen).toBeFalse();
  });
});
