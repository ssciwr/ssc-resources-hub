import {$,escapeHtml} from './dom.js';
import {roles} from './data-loader.js';
import {prereq,alternatives,recommendations,conditionalPrerequisites} from './dependencies.js';
export function audience(c){return c.roles.length===4?'All learners':c.roles.map(r=>roles[r]).join(', ')}

function prerequisiteSummary(id) {
  const choices = alternatives(id);
  const required = [...prereq(id), ...(choices.length ? ['Any one: ' + choices.join(' or ')] : [])].join(', ');
  const conditional = conditionalPrerequisites(id).map(
    ({course, when}) => `Conditional: ${course} (${when})`
  );
  const recommended = recommendations(id);
  return [required, ...conditional, ...(recommended.length ? ['Recommended: ' + recommended.join(', ')] : [])]
    .filter(Boolean).join(' · ') || 'None shown';
}

export function renderCatalogue(found){$('catalogue').innerHTML=found.map(c=>`<tr><td>${escapeHtml(c.id)}</td><td><a href="#${escapeHtml(c.id)}" data-open="${escapeHtml(c.id)}">${escapeHtml(c.name)}</a></td><td title="${escapeHtml(c.roles.map(r=>roles[r]).join(', '))}">${escapeHtml(audience(c))}</td><td>${escapeHtml(prerequisiteSummary(c.id))}</td></tr>`).join('');$('empty').hidden=found.length!==0;}
