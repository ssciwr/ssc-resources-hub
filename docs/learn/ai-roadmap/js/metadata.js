import {$} from './dom.js';
import {manifest, courses, goals, audiences} from './data-loader.js';

export function renderMetadata() {
  const mvp = new Set(courses.filter(course => course.mvp).map(course => course.id));
  const equivalentOptions = manifest.equivalent_course_groups.reduce((count, group) =>
    count + Math.max(0, group.filter(id => mvp.has(id)).length - 1), 0);
  const maximum = Math.max(...courses.map(course => course.duration_minutes));
  const version = `v${manifest.version.replaceAll('-', ' ')} · Curriculum v${manifest.baseline}`;
  $('courseCount').textContent = courses.length;
  $('mvpCount').textContent = mvp.size;
  $('mvpSummary').textContent = `MVP options (${mvp.size - equivalentOptions} distinct competencies)`;
  $('goalCount').textContent = Object.keys(goals).filter(id => id !== 'F').length;
  $('durationCap').textContent = maximum % 60 === 0 ? `${maximum / 60}h` : `${maximum}min`;
  $('roadmapVersion').textContent = version;
  $('roadmapFooterVersion').textContent = version;
  const definitions = $('audienceDefinitions');
  definitions.replaceChildren();
  for (const audience of Object.values(audiences)) {
    const term = document.createElement('dt');
    const description = document.createElement('dd');
    term.textContent = audience.label;
    description.textContent = audience.help;
    definitions.append(term, description);
  }
}
