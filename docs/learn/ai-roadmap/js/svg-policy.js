// Mirror the public layout schema at the DOM boundary: fail closed on active SVG.
const tags = new Set(['svg', 'defs', 'g', 'rect', 'text', 'polyline', 'circle', 'marker', 'path', 'title']);
const attributes = new Set([
  'aria-label', 'class', 'cx', 'cy', 'd', 'data-a', 'data-b', 'data-gate', 'data-goal',
  'data-id', 'fill', 'height', 'id', 'marker-end', 'markerHeight', 'markerUnits',
  'markerWidth', 'orient', 'points', 'r', 'refX', 'refY', 'role', 'rx', 'stroke',
  'stroke-dasharray', 'stroke-linecap', 'stroke-linejoin', 'stroke-width', 'tabindex',
  'text-anchor', 'viewBox', 'width', 'x', 'y',
]);
const colour = /^(?:[a-zA-Z]+|#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8}))$/;
const marker = /^(?:none|url\(#[a-zA-Z][a-zA-Z0-9_.:-]*\))$/;

export function assertSafeSvg(spec) {
  if (!tags.has(spec.tag)) throw new Error('Unsupported SVG tag');
  for (const [name, value] of Object.entries(spec.attrs || {})) {
    if (!attributes.has(name) || typeof value !== 'string') throw new Error('Unsupported SVG attribute');
    if (['fill', 'stroke'].includes(name) && !colour.test(value)) throw new Error('Unsupported SVG colour');
    if (name === 'marker-end' && !marker.test(value)) throw new Error('Only local SVG markers are supported');
  }
  for (const child of spec.children || []) assertSafeSvg(child);
}
