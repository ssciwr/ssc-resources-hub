import {edges} from './data-loader.js';
export const prereq=id=>edges.filter(e=>e[1]===id&&!['conditional','alternative','recommended'].includes(e[3])).map(e=>e[0]);export const next=id=>edges.filter(e=>e[0]===id&&!['conditional','alternative','recommended'].includes(e[3])).map(e=>e[1]);
export const recommendations=id=>edges.filter(e=>e[1]===id&&e[3]==='recommended').map(e=>e[0]);export const alternatives=id=>edges.filter(e=>e[1]===id&&e[3]==='alternative').map(e=>e[0]);export const altNext=id=>edges.filter(e=>e[0]===id&&e[3]==='alternative').map(e=>e[1]);

export const conditionalPrerequisites = id => edges
  .filter(edge => edge[1] === id && edge[3] === 'conditional')
  .map(([course, , when]) => ({course, when}));

export const conditionalNext = id => edges
  .filter(edge => edge[0] === id && edge[3] === 'conditional')
  .map(([, course, when]) => ({course, when}));
