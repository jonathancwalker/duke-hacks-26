// Privacy notice: the event's short consent text (events/*.json "consent", via /api/event), shown while the station
// waits for a visitor. Self-contained: it brings its own styles and imports nothing, so any screen can place it.
//
//   showConsent(S.event.consent)              // default: a small panel pinned top-left, under the header
//   showConsent(S.event.consent, someElement) // placed inside someElement; that screen decides where it sits
//   hideConsent()                             // while a visit runs
//
// The printable sign with the full wording lives in PRIVACY.md.

let box = null;

const CSS = `
.consent { font: 12px/1.45 Inter, system-ui, sans-serif; color: #c9bfae; max-width: 34em; }
.consent p { margin: 0 0 5px; } .consent p:last-child { margin: 0; }
.consent[hidden] { display: none; }
.consent.pinned { position: absolute; top: 68px; left: 28px; z-index: 5; padding: 10px 14px; border-radius: 10px;
                  background: #14110ee0; border: 1px solid #3a332b; }
@media (max-width: 700px) { .consent.pinned { left: 16px; right: 16px; max-width: none; } }`;

export function showConsent(text, parent) {
  if (!text) return hideConsent();
  if (!box) {
    document.head.append(Object.assign(document.createElement('style'), { textContent: CSS }));
    box = Object.assign(document.createElement('aside'), { className: 'consent' });
    box.setAttribute('aria-label', 'Privacy');
  }
  box.replaceChildren(...text.split('\n').map(line => Object.assign(document.createElement('p'), { textContent: line })));
  box.classList.toggle('pinned', !parent);
  (parent || document.body).append(box);          // moves it if it was already placed elsewhere
  box.hidden = false;
}

export function hideConsent() { if (box) box.hidden = true; }
