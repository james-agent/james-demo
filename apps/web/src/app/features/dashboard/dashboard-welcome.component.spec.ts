import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DashboardWelcomeComponent } from './dashboard-welcome.component';

describe('DashboardWelcomeComponent', () => {
  let fixture: ComponentFixture<DashboardWelcomeComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DashboardWelcomeComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(DashboardWelcomeComponent);
    fixture.detectChanges();
  });

  it('displays welcome headline and subtext', () => {
    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.querySelector('.welcome__headline')?.textContent?.trim()).toBe(
      'Welcome back',
    );
    expect(compiled.querySelector('.welcome__subtext')?.textContent?.trim()).toBe(
      'Your CRM dashboard is ready',
    );
  });
});
