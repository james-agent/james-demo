import {
  Directive,
  ElementRef,
  HostListener,
  Input,
  Renderer2,
  booleanAttribute,
  inject,
} from '@angular/core';

@Directive({
  selector: '[appComingSoon]',
  standalone: true,
})
export class ComingSoonDirective {
  @Input({ alias: 'appComingSoon', transform: booleanAttribute })
  active = false;

  private readonly elementRef = inject(ElementRef<HTMLElement>);
  private readonly renderer = inject(Renderer2);
  private tooltipEl: HTMLElement | null = null;

  @HostListener('mouseenter')
  @HostListener('click', ['$event'])
  onInteract(event?: Event): void {
    if (!this.active) {
      return;
    }
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }
    this.showTooltip();
  }

  @HostListener('mouseleave')
  onLeave(): void {
    if (!this.active) {
      return;
    }
    this.hideTooltip();
  }

  private showTooltip(): void {
    if (this.tooltipEl) {
      return;
    }

    const host = this.elementRef.nativeElement;
    this.tooltipEl = this.renderer.createElement('span');
    this.renderer.addClass(this.tooltipEl, 'coming-soon-tooltip');
    this.renderer.setProperty(this.tooltipEl, 'textContent', 'Coming soon');
    this.renderer.setAttribute(this.tooltipEl, 'role', 'tooltip');
    this.renderer.appendChild(host, this.tooltipEl);
  }

  private hideTooltip(): void {
    if (!this.tooltipEl) {
      return;
    }

    const host = this.elementRef.nativeElement;
    this.renderer.removeChild(host, this.tooltipEl);
    this.tooltipEl = null;
  }
}
