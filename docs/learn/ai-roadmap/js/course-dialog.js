import {$, root, escapeHtml as h, safeHttpsUrl, citationHtml} from './dom.js';
import {byId, goals, roles, courseBibliography, referenceLibrary, prerequisiteRationale} from './data-loader.js';
import {prereq, next, alternatives, altNext, recommendations, conditionalPrerequisites, conditionalNext} from './dependencies.js';
import {canvas} from './graph.js';

function instructorSection(course) {
  const cards = course.instructors.map(instructor => {
    const avatar = safeHttpsUrl(instructor.avatar);
    const github = safeHttpsUrl(instructor.github);
    const source = safeHttpsUrl(instructor.source);
    return `<li class="instructor-card">
      <span class="instructor-avatar" aria-hidden="true"><span>${h(instructor.initials)}</span>
        ${avatar ? `<img src="${h(avatar)}" alt="" width="64" height="64" referrerpolicy="no-referrer">` : ''}
      </span>
      <div class="instructor-info"><strong>${h(instructor.name)}</strong>
        ${instructor.position ? `<span class="instructor-position">${h(instructor.position)}</span>` : ''}
        <small>${h(instructor.affiliation)}</small>
        <div class="instructor-links">
          ${github ? `<a href="${h(github)}" target="_blank" rel="noopener noreferrer">GitHub · @${h(instructor.githubHandle || 'profile')} ↗</a>` : ''}
          ${source ? `<a href="${h(source)}" target="_blank" rel="noopener noreferrer">Official course page ↗</a>` : ''}
        </div>
      </div>
    </li>`;
  }).join('');
  return `<section class="detail-section instructors-section"><h3>Instructors</h3>
    ${cards ? `<ul class="instructor-list">${cards}</ul>` : '<p class="instructor-pending">To be confirmed.</p>'}
  </section>`;
}

export function openCourse(id) {
  if (!Object.hasOwn(byId, id)) return;
  const c = byId[id];
  for (const element of canvas.querySelectorAll('.course-link')) {
    element.classList.toggle('selected', element.dataset.id === id);
  }
  $('detailMeta').innerHTML = `<div class="detail-kicker">
    <span class="tag ${c.mvp ? 'mvp' : ''}">${c.mvp ? 'MVP candidate' : 'Future course'}</span>
    <span>${h(c.id)} · ${h(goals[c.goal])}</span><span class="sep">|</span><span>Up to 4 hours</span>
  </div>`;
  $('detailTitle').textContent = c.name;
  const bullets = items => `<ul class="detail-list">${items.map(item => `<li>${h(item)}</li>`).join('')}</ul>`;
  const links = ids => ids.length ? `<ul class="detail-list">${ids.map(courseId =>
    `<li><button class="link" data-open="${h(courseId)}">${h(courseId)} · ${h(byId[courseId].name)}</button></li>`
  ).join('')}</ul>` : '<p class="empty-list">None</p>';
  const conditions = conditionalPrerequisites(id), enabledConditions = conditionalNext(id);
  const conditionalLinks = items => items.map(({course, when}) =>
    `<div class="conditional-relation"><p class="conditional-note">Conditional: ${h(when)}</p>${links([course])}</div>`
  ).join('');
  const bibliography = courseBibliography[id].map((key, index) => {
    const reference = referenceLibrary[key];
    const url = safeHttpsUrl(reference.url);
    return `<li><span class="bib-num">[${index + 1}]</span><div>${citationHtml(reference.citation)}
      ${url ? `<a href="${h(url)}" target="_blank" rel="noopener noreferrer" aria-label="Open reference ${index + 1} in a new tab">${h(reference.url)}<span class="external-mark" aria-hidden="true">↗</span></a>` : ''}
    </div></li>`;
  }).join('');
  $('detailBody').innerHTML = `
    <section class="detail-section prereq-card"><h3>Prerequisites</h3>
      <div class="prereq-grid"><div><h4>SSC AI courses</h4>
        ${prereq(id).length ? links(prereq(id)) : alternatives(id).length || conditions.length ? '' : links([])}
        ${alternatives(id).length ? `<p class="choice-note">Complete any one (or equivalent competency):</p>${links(alternatives(id))}` : ''}
        ${recommendations(id).length ? `<p class="recommended-note">Recommended, not mandatory:</p>${links(recommendations(id))}` : ''}
        ${conditionalLinks(conditions)}
      </div><div><h4>Prior knowledge &amp; setup</h4>${bullets(c.prior)}</div></div>
      <p class="prereq-note"><strong>Why these prerequisites?</strong> ${h(prerequisiteRationale[id])}</p>
      <p class="prereq-note">Equivalent prior competencies are accepted; attending prerequisite courses is not mandatory.</p>
    </section>
    <section class="detail-section"><h3>Description</h3><p class="description-copy">${h(c.description)}</p></section>
    ${instructorSection(c)}
    <section class="detail-section"><h3>About this course</h3><div class="about-grid">
      <div><h4>What you will learn</h4>${bullets(c.learn)}</div>
      <div class="about-tools"><h4>Tools you will learn</h4><ul class="tools">${c.tools.map(tool => `<li>${h(tool)}</li>`).join('')}</ul>
        <p class="tools-note">Proposed teaching tools; final selection is subject to SSC review.</p>
      </div>
    </div></section>
    <section class="detail-section"><h3>Modules</h3><ol class="module-list">${c.modules.map((module, index) =>
      `<li><span class="module-number" aria-hidden="true">${String(index + 1).padStart(2, '0')}</span>
        <span class="module-copy"><strong>${h(module)}</strong><small>${h(c.moduleDescriptions[index])}</small></span>
      </li>`
    ).join('')}</ol></section>
    ${c.practice ? `<section class="detail-section"><h3>Practical project</h3><p>${h(c.practice)}</p><h4>Acceptance criteria</h4><p>${h(c.acceptance)}</p></section>` : ''}
    <div class="detail-bottom">
      <section class="detail-section"><h3>Intended learners</h3><p>${h(c.roles.length === 4 ? 'All learner categories' : c.roles.map(role => roles[role]).join(', '))}</p></section>
      <section class="detail-section"><h3>Enables</h3>
        ${next(id).length ? links(next(id)) : altNext(id).length || enabledConditions.length ? '' : links([])}
        ${altNext(id).length ? `<p class="choice-note">One alternative pathway into:</p>${links(altNext(id))}` : ''}
        ${conditionalLinks(enabledConditions)}
      </section>
      <section class="detail-section"><h3>Material reuse / readiness</h3><p><strong>${h(c.coverage)} coverage</strong> · ${h(c.courseType)} course</p></section>
    </div>
    <section class="detail-section bibliography"><h3>Learner bibliography</h3>
      <p class="bib-intro">Recommended readings and technical references · IEEE-style numbering · Not required before the course. Tool-specific readings follow the selected implementation; the proposed list remains subject to SSC review.</p>
      <ol class="bib-list">${bibliography}</ol>
    </section>
    <p class="detail-note">Draft course specification · Learning outcomes, tools and modules are subject to curriculum validation.</p>`;
  for (const image of $('detailBody').querySelectorAll('.instructor-avatar img')) {
    image.addEventListener('error', () => { image.hidden = true; }, {once: true});
  }
  if (!$('detail').open) $('detail').showModal();
  $('detail').scrollTop = 0;
  $('detailTitle').focus({preventScroll: true});
}

root.addEventListener('click', event => {
  const link = event.target.closest('[data-open]');
  if (link) {
    event.preventDefault();
    openCourse(link.dataset.open);
  }
});
$('close').onclick = () => $('detail').close();
$('detail').addEventListener('click', event => {
  if (event.target === $('detail')) $('detail').close();
});
$('detail').addEventListener('close', () => {
  canvas.querySelectorAll('.selected').forEach(element => element.classList.remove('selected'));
});
