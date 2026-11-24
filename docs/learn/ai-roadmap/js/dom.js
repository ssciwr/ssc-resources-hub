export const root = document.getElementById('ssc-roadmap');
export const $ = id => root.querySelector('#'+CSS.escape(id));

export function escapeHtml(value) {
  const entities = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'};
  return String(value).replace(/[&<>"']/g, character => entities[character]);
}

export function safeHttpsUrl(value) {
  if (typeof value !== 'string' || /[\s\u0000-\u001f\u007f<>"\\]/.test(value)) return '';
  try {
    const url = new URL(value);
    return url.protocol === 'https:' && url.hostname && !url.username && !url.password ? url.href : '';
  } catch {
    return '';
  }
}

// Citations support exact <em> tokens, not arbitrary HTML. Everything else is text.
export function citationHtml(value) {
  const container = document.createElement('span');
  let current = container;
  for (const token of String(value).split(/(<\/?em>)/i)) {
    if (token.toLowerCase() === '<em>') {
      const emphasis = document.createElement('em');
      current.append(emphasis);
      current = emphasis;
    } else if (token.toLowerCase() === '</em>' && current !== container) {
      current = current.parentElement;
    } else {
      current.append(document.createTextNode(token));
    }
  }
  return container.innerHTML;
}
