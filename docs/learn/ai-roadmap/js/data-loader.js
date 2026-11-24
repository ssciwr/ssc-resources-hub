const read = async (path) => {
  const response = await fetch(new URL('../data/' + path, import.meta.url));
  if (!response.ok) throw new Error(`Cannot load ${path}: ${response.status}`);
  return response.json();
};
const [manifest, goals, audiences, dependencies, referenceLibrary, instructors, layout] = await Promise.all(
  ['roadmap.json','learning-goals.json','audiences.json','dependencies.json','bibliography.json','instructors.json','layout.json'].map(read)
);
const rawCourses = await Promise.all(manifest.course_ids.map(id => read(`courses/${id}.json`)));
export const courses = rawCourses.map(c => ({...c, instructors: c.instructors.map(id => instructors[id])}));
export const byId = Object.fromEntries(courses.map(c => [c.id,c]));
export const roles = Object.fromEntries(Object.entries(audiences).map(([id,a])=>[id,a.label]));
export const audienceHelp = Object.fromEntries(Object.entries(audiences).map(([id,a])=>[id,a.help]));
export const courseBibliography = Object.fromEntries(courses.map(c=>[c.id,c.references]));
export const prerequisiteRationale = Object.fromEntries(courses.map(c=>[c.id,c.prerequisiteRationale]));
export const edges = Object.entries(dependencies).flatMap(([target,d]) => [
  ...d.all_of.map(id=>[id,target,'','required']),
  ...d.any_of.flat().map(id=>[id,target,'','alternative']),
  ...d.recommended.map(id=>[id,target,'','recommended']),
  ...d.conditional.map(({course,when})=>[course,target,when,'conditional'])
]);
export { manifest, goals, audiences, dependencies, referenceLibrary, layout };
