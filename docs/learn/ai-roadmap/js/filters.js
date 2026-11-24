import {$,root} from './dom.js';
import {courses,goals,roles,audienceHelp,edges} from './data-loader.js';
import {highlight} from './graph.js';
import {renderCatalogue} from './catalogue.js';
for(const [id,label] of Object.entries(goals))$('goal').add(new Option(id==='F'?label:id+' · '+label,id));
const audienceChoices=[['','All learners','Show the complete roadmap'],...Object.entries(roles).map(([id,label])=>[id,label,audienceHelp[id]])];
for(const [id,label,help] of audienceChoices){const item=document.createElement('label');item.className='audience-option';item.innerHTML=`<input type="radio" name="audienceChoice" value="${id}" ${id===''?'checked':''}><span><strong>${label}</strong><small>${help}</small></span>`;$('learners').append(item);item.querySelector('input').addEventListener('change',()=>{setAudience(id);refresh()});item.addEventListener('click',e=>{if(e.target.matches('input')&&e.detail>0){setAudience(id);closeAudience(true);refresh()}})}
function setAudience(id){$('role').value=id;const label=roles[id]||'All learners';$('roleLabel').textContent=label;$('roleToggle').setAttribute('aria-label','Intended audience: '+label);for(const radio of $('learners').querySelectorAll('input'))radio.checked=radio.value===id;}
function closeAudience(focus=false){$('audienceOptions').hidden=true;$('roleToggle').setAttribute('aria-expanded','false');if(focus)$('roleToggle').focus()}
$('roleToggle').addEventListener('click',()=>{if(!$('audienceOptions').hidden){closeAudience();return}$('audienceOptions').hidden=false;$('roleToggle').setAttribute('aria-expanded','true');$('learners').querySelector('input:checked').focus()});
$('audiencePicker').addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('audienceOptions').hidden){e.preventDefault();closeAudience(true)}else if(e.key==='Enter'&&e.target.matches('input[type=radio]')){e.preventDefault();setAudience(e.target.value);closeAudience(true);refresh()}});
document.addEventListener('pointerdown',e=>{if(!$('audiencePicker').contains(e.target))closeAudience()});
$('audiencePicker').addEventListener('focusout',e=>{if(e.relatedTarget&&!$('audiencePicker').contains(e.relatedTarget))closeAudience()});

function matches(c){const g=$('goal').value,r=$('role').value,q=$('search').value.trim().toLowerCase();if(q)return `${c.id} ${c.name} ${c.outcome} ${c.description} ${c.learn.join(" ")} ${c.tools.join(" ")} ${c.modules.join(" ")} ${c.moduleDescriptions.join(" ")}`.toLowerCase().includes(q);let goalOK=!g||c.goal===g;if(g&&g!=='F'){const ancestors=new Set(courses.filter(x=>x.goal===g).map(x=>x.id));let changed=true;while(changed){changed=false;for(const [a,b,_,kind] of edges)if(kind!=='conditional'&&kind!=='recommended'&&ancestors.has(b)&&!ancestors.has(a)){ancestors.add(a);changed=true}}goalOK=ancestors.has(c.id)}return goalOK&&(!r||c.roles.includes(r))}
export function refresh(){
 const found=courses.filter(matches),ids=new Set(found.map(c=>c.id));
 const searching=!!$('search').value.trim();highlight(ids,searching?'':$('goal').value);
 $('matchCount').textContent=searching?`${found.length} of ${courses.length} courses match search · all goals and audiences`:`${found.length} of ${courses.length} courses match filters`;
 renderCatalogue(found);
}
export function bindFilters(){for(const id of ['goal','role','search'])$(id).addEventListener('input',refresh);$('reset').onclick=()=>{for(const id of ['goal','search'])$(id).value='';setAudience('');closeAudience();refresh()};}
