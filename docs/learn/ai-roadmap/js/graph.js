import {layout, byId, edges} from './data-loader.js';
import {$} from './dom.js';
import {assertSafeSvg} from './svg-policy.js';
const ns='http://www.w3.org/2000/svg';
function make(spec){
  const node=document.createElementNS(ns,spec.tag);
  for(const [key,value] of Object.entries(spec.attrs||{}))node.setAttribute(key,value);
  if(spec.text!==undefined)node.textContent=spec.text;
  for(const child of spec.children||[])node.append(make(child));
  if(spec.course_id){
    const c=byId[spec.course_id];
    node.setAttribute('aria-label',`${c.name} — open course details`);
    node.querySelector('title').textContent=c.name;
    const status=node.querySelector('.node-status');
    status.textContent=c.mvp?'MVP':'FUTURE';
    const accent=c.mvp?'#007d7a':'#397c9f';
    node.querySelector('rect').setAttribute('fill',c.mvp?'#e1f3ee':'#eaf3f8');
    node.querySelector('rect').setAttribute('stroke',accent);
    node.querySelector('.node-id').setAttribute('fill',accent);status.setAttribute('fill',accent);
    // Short titles and line breaks are a layout choice. If course title changes, use the new title.
    if(c.name!==spec.baseline_title){
      const labels=[...node.querySelectorAll('.node-title')];
      const first=labels[0];if(first){first.textContent=c.name;labels.slice(1).forEach(n=>n.remove());}
    }
  }
  return node;
}
export const canvas=$('canvas');
const spec={tag:'svg',attrs:layout.svg,children:layout.elements};
assertSafeSvg(spec);
export const overview=make(spec);
$('mapMount').replaceWith(overview);
export function bindGraph(openCourse){
  for(const el of canvas.querySelectorAll('.course-link')){
    el.addEventListener('click',()=>openCourse(el.dataset.id));
    el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();openCourse(el.dataset.id)}});
  }
}
export function highlight(ids,goal){
  for(const el of canvas.querySelectorAll('.course-link'))el.classList.toggle('dim',!ids.has(el.dataset.id));
  for(const el of overview.querySelectorAll('.flow-edge'))el.classList.toggle('dim',!!((byId[el.dataset.a]&&!ids.has(el.dataset.a))||(byId[el.dataset.b]&&!ids.has(el.dataset.b))));
  for(const p of canvas.querySelectorAll('.lane-bg'))p.classList.toggle('dim',!!goal&&p.dataset.goal!==goal);
  for(const p of canvas.querySelectorAll('.choice-gate')){
    const gate='gate-'+p.dataset.gate;
    const members=layout.elements.filter(e=>e.attrs['data-a']===gate||e.attrs['data-b']===gate).flatMap(e=>[e.attrs['data-a'],e.attrs['data-b']]);
    p.classList.toggle('dim',!members.some(i=>ids.has(i)));
  }
}
let mapScale=1,fitMode=true;const width=Number(layout.svg.width);
function setZoom(value){mapScale=Math.min(2,Math.max(.15,value));overview.style.width=(width*mapScale)+'px';$('zoomLevel').textContent=Math.round(mapScale*100)+'%'}
function fitMap(){fitMode=true;setZoom((canvas.clientWidth-parseFloat(getComputedStyle(canvas).paddingLeft)-parseFloat(getComputedStyle(canvas).paddingRight))/width);canvas.scrollLeft=0}
export function bindZoom(){
  $('zoomIn').onclick=()=>{fitMode=false;setZoom(mapScale*1.2)};
  $('zoomOut').onclick=()=>{fitMode=false;setZoom(mapScale/1.2)};
  $('fitMap').onclick=fitMap;$('actualSize').onclick=()=>{fitMode=false;setZoom(1)};
  new ResizeObserver(()=>{if(fitMode)fitMap()}).observe(canvas);fitMap();
}
