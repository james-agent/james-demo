import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';

import { LeadListComponent } from './lead-list.component';

describe('LeadListComponent', () => {
  let fixture: ComponentFixture<LeadListComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LeadListComponent, FormsModule],
    }).compileComponents();

    fixture = TestBed.createComponent(LeadListComponent);
  });

  it('renders Leads title and mock rows', fakeAsync(() => {
    fixture.detectChanges();
    tick(200);
    fixture.detectChanges();

    const title = fixture.nativeElement.querySelector('h1') as HTMLElement;
    expect(title.textContent?.trim()).toBe('Leads');

    const rows = fixture.nativeElement.querySelectorAll('.crm-list__table tbody tr');
    expect(rows.length).toBe(10);
  }));
});
