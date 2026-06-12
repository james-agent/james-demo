import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-inception-shell',
  standalone: true,
  imports: [RouterOutlet],
  template: `
    <div class="inception-shell">
      <main class="inception-shell__main">
        <router-outlet />
      </main>
    </div>
  `,
  styles: [
    `
      .inception-shell {
        min-height: 100vh;
        background: var(--crm-bg-main, #ffffff);
      }
      .inception-shell__main {
        min-height: 100vh;
      }
    `,
  ],
})
export class InceptionShellComponent {}
