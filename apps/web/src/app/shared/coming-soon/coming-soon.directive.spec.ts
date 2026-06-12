import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { ComingSoonDirective } from './coming-soon.directive';

@Component({
  standalone: true,
  imports: [ComingSoonDirective],
  template: `<button type="button" [appComingSoon]="true">Leads</button>`,
})
class HostComponent {}

describe('ComingSoonDirective', () => {
  let fixture: ComponentFixture<HostComponent>;
  let routerNavigateSpy: jasmine.Spy;

  beforeEach(async () => {
    routerNavigateSpy = jasmine.createSpy('navigate');

    await TestBed.configureTestingModule({
      imports: [HostComponent],
      providers: [{ provide: Router, useValue: { navigate: routerNavigateSpy } }],
    }).compileComponents();

    fixture = TestBed.createComponent(HostComponent);
    fixture.detectChanges();
  });

  it('shows Coming soon tooltip on click without navigation', () => {
    const button = fixture.nativeElement.querySelector('button') as HTMLButtonElement;

    button.click();
    fixture.detectChanges();

    const tooltip = button.querySelector('.coming-soon-tooltip');
    expect(tooltip?.textContent?.trim()).toBe('Coming soon');
    expect(routerNavigateSpy).not.toHaveBeenCalled();
  });
});
