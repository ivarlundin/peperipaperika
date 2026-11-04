/** LCD title text + overflow marquee (CSS translateX, measured in JS). */

const MARQUEE_GAP_PX = 56;
/** Pixels scrolled per second when title overflows. */
const MARQUEE_SPEED_PX_S = 24;

/**
 * @param {HTMLElement | null} root `#lcd-title`
 */
export function createLcdTitle(root) {
  if (!root) {
    return { setText() {}, refresh() {} };
  }

  const initial = root.textContent.trim();

  const viewport = document.createElement('span');
  viewport.className = 'nl-lcd-title-viewport';

  const track = document.createElement('span');
  track.className = 'nl-lcd-title-track';

  const segmentA = document.createElement('span');
  segmentA.className = 'nl-lcd-title-segment';

  const gap = document.createElement('span');
  gap.className = 'nl-lcd-title-gap';
  gap.setAttribute('aria-hidden', 'true');

  const segmentB = document.createElement('span');
  segmentB.className = 'nl-lcd-title-segment nl-lcd-title-segment--dup';
  segmentB.setAttribute('aria-hidden', 'true');

  track.append(segmentA, gap, segmentB);
  viewport.append(track);
  root.replaceChildren(viewport);

  let currentText = initial;
  segmentA.textContent = initial;
  segmentB.textContent = initial;

  const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

  function refresh() {
    const viewWidth = viewport.clientWidth;
    const textWidth = segmentA.scrollWidth;
    const overflows = textWidth > viewWidth + 1;
    const reducedMotion = motionQuery.matches;

    root.classList.toggle('is-overflow', overflows);
    root.classList.toggle('is-marquee-active', overflows && !reducedMotion);

    track.classList.remove('is-marquee');
    track.style.transform = '';
    track.style.removeProperty('--nl-lcd-marquee-shift');
    track.style.removeProperty('--nl-lcd-marquee-duration');

    gap.hidden = true;
    segmentB.hidden = true;

    if (!overflows || reducedMotion) {
      return;
    }

    gap.hidden = false;
    segmentB.hidden = false;
    segmentB.textContent = currentText;

    const shift = textWidth + MARQUEE_GAP_PX;
    track.style.setProperty('--nl-lcd-marquee-shift', `${shift}px`);
    track.style.setProperty(
      '--nl-lcd-marquee-duration',
      `${Math.max(8, shift / MARQUEE_SPEED_PX_S)}s`,
    );
    track.classList.add('is-marquee');
  }

  function setText(text) {
    currentText = text;
    segmentA.textContent = text;
    segmentB.textContent = text;
    refresh();
  }

  const resizeObserver = new ResizeObserver(() => refresh());
  resizeObserver.observe(viewport);
  resizeObserver.observe(root);

  motionQuery.addEventListener('change', refresh);
  window.addEventListener('resize', refresh, { passive: true });

  requestAnimationFrame(refresh);

  return { setText, refresh };
}
