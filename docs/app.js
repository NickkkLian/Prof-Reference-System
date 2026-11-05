const $ = selector => document.querySelector(selector);
const students = window.SAMPLE.map(student => ({...student,course:student.course.replace('DEMO','Course'),written:false,notes:''}));
let selected = students[0];
let folder = 'waiting';
let lastWritten;
function render() {
  const written = folder === 'written';
  const visible = students.filter(student => student.written === written);
  $('#waiting-count').textContent = students.filter(student => !student.written).length;
  $('#written-count').textContent = students.filter(student => student.written).length;
  $('#queue-summary').textContent = written ? `${visible.length} letters written` : `${visible.length} waiting for a letter`;
  for (const name of ['waiting','written']) $(`#${name}-folder`).toggleAttribute('aria-current',name===folder);
  $('#student-list').replaceChildren();
  visible.forEach(student => {
    const row = document.createElement('button');
    row.className = 'student-row';
    row.setAttribute('aria-pressed', String(student===selected));
    row.innerHTML=`<strong>${student.name}</strong><small>${student.course}, section ${student.section}</small><div class="student-meta"><span class="badge success">Conditions met</span><span class="document-dots" aria-label="2 missing documents"><i></i><i></i> No files</span></div>`;
    row.addEventListener('click',()=>{selected=student;render();ui.fade($('.record-content'));});
    $('#student-list').append(row);
  });
  $('#empty-record').hidden = Boolean(selected);
  $('.record-content').hidden = !selected;
  if (!selected) {
    $('#empty-record h1').textContent = written ? 'No letters written yet' : 'Every letter is written';
    $('#empty-record p').textContent = written ? 'Choose Waiting to open a student record.' : 'Open Written to review a letter.';
    return;
  }
  $('#student-name').textContent=selected.name;
  $('#student-number').textContent=`${selected.course}, section ${selected.section}`;
  $('#grade').textContent=`${selected.grade}%`;
  $('#attendance').textContent=`${selected.attendance}%`;
  $('#grade-bar').style.width=`${selected.grade}%`;
  $('#attendance-bar').style.width=`${selected.attendance}%`;
  $('#notes').value=selected.notes;
  $('#mark-written').textContent=selected.written?'Move back to waiting':'Mark letter written';
  $('#record-status').textContent=selected.written?'Letter recorded as written.':'Letter waiting to be written.';
}
$('#start-notes').addEventListener('click',()=>{
  $('#notes').focus();
  ui.fade($('#notes-section'));
  $('#record-status').textContent='Letter notes are open for this student.';
});
$('#notes').addEventListener('input',event=>{if(selected)selected.notes=event.target.value;});
document.querySelectorAll('[data-prompt]').forEach(button=>button.addEventListener('click',()=>{
  if (!selected) return;
  selected.notes += `${selected.notes?'\n\n':''}${button.dataset.prompt}\n`;
  $('#notes').value=selected.notes;
  $('#notes').focus();
}));
$('#mark-written').addEventListener('click',()=>{
  if (!selected) return;
  selected.written=!selected.written;
  lastWritten=selected;
  $('#undo-toast span').textContent=selected.written?'Letter marked written':'Letter moved to waiting';
  $('#undo-toast').hidden=false;
  ui.fade($('#undo-toast'));
  selected=students.find(student=>student.written===(folder==='written'))||null;
  render();
  ui.fade($('#student-list'));
});
$('#undo').addEventListener('click',()=>{
  lastWritten.written=!lastWritten.written;
  folder=lastWritten.written?'written':'waiting';
  selected=lastWritten;
  $('#undo-toast').hidden=true;
  render();
  ui.fade($('.record-content'));
});
for(const name of ['waiting','written']) $(`#${name}-folder`).addEventListener('click',()=>{
  folder=name;
  selected=students.find(student=>student.written===(name==='written'))||null;
  render();
  ui.fade($('#student-list'));
});
document.addEventListener('keydown',event=>{
  if (!['j','k'].includes(event.key.toLowerCase())||event.target.closest('input,textarea,select'))return;
  const visible=students.filter(student=>student.written===(folder==='written'));
  const position=visible.indexOf(selected);
  selected=visible[Math.max(0,Math.min(visible.length-1,position+(event.key.toLowerCase()==='j'?1:-1)))]||null;
  render();
});
render();
document.documentElement.dataset.ready='true';
