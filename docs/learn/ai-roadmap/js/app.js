import {bindGraph,bindZoom} from './graph.js';
import {openCourse} from './course-dialog.js';
import {bindFilters,refresh} from './filters.js';
import {byId} from './data-loader.js';
bindGraph(openCourse);bindZoom();bindFilters();refresh();if(Object.hasOwn(byId,location.hash.slice(1)))openCourse(location.hash.slice(1));
