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
    row.innerHTML=`<strong>${student.name}</strong><small>${student.course}, section ${student.section}</small>`;
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
  $('#grade-source').textContent = 'Grade from the roster · attendance from course records';
  $('#evidence-preview').replaceChildren();
  if (selected.number === '10001001') {
    for (const [title, text] of [
      ['Transcript preview', 'Fictional transcript · Alice Chen, 10001001. DEMO 310, section 101, Fall 2025. Final grade: 88.5%. The roster supplies the eligibility grade; this sample transcript agrees.'],
      ['Interest statement', 'Fictional statement · I am applying to a graduate program in human-computer interaction. In DEMO 310, I built and evaluated an accessible course-planning prototype. I hope to study how students navigate complex academic requirements. I would value a reference about my research process and response to feedback.']
    ]) {
      const details=document.createElement('details');
      const summary=document.createElement('summary'); summary.textContent=title;
      const copy=document.createElement('p'); copy.textContent=text;
      details.append(summary,copy); $('#evidence-preview').append(details);
    }
    const note=document.createElement('p'); note.textContent='Fictional documents created for this demo.'; $('#evidence-preview').append(note);
  }
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
  if ($('#faculty-desk').hidden) return;
  if (!['j','k'].includes(event.key.toLowerCase())||event.target.closest('input,textarea,select'))return;
  const visible=students.filter(student=>student.written===(folder==='written'));
  const position=visible.indexOf(selected);
  selected=visible[Math.max(0,Math.min(visible.length-1,position+(event.key.toLowerCase()==='j'?1:-1)))]||null;
  render();
});
function showWorkspace(checking) {
  $('#eligibility-desk').hidden = !checking;
  $('#faculty-desk').hidden = checking;
  $('.folders').hidden = checking;
  for (const [id, active] of [['check-view',checking],['queue-view',!checking]]) {
    if (active) $('#' + id).setAttribute('aria-current','page'); else $('#' + id).removeAttribute('aria-current');
  }
  $('.skip').href = checking ? '#eligibility-main' : '#main';
}
$('#check-view').addEventListener('click', () => showWorkspace(true));
$('#queue-view').addEventListener('click', () => { showWorkspace(false); render(); });
const sourceLabels = { database: 'Roster grade', transcript: 'Fictional transcript extraction', manual: 'Manual entry (no extracted PDF grade)' };
let currentCase;
function chooseCase(student) {
  currentCase = student;
  document.querySelectorAll('[data-case]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.case === student.id)));
  $('#case-name').textContent = student.name;
  $('#case-number').textContent = 'Student ' + student.number;
  $('#case-evidence').replaceChildren();
  for (const [label, value] of [['Roster', student.enrolments.length ? student.enrolments.length + ' matching enrolment' + (student.enrolments.length > 1 ? 's' : '') : 'No matching enrolments'], ['Overall grade', student.grade + '% · 80% required'], ['Grade source', sourceLabels[student.grade_source]]]) {
    const row=document.createElement('div'); const dt=document.createElement('dt'); const dd=document.createElement('dd');
    dt.textContent=label; dd.textContent=value; row.append(dt,dd); $('#case-evidence').append(row);
  }
  $('#case-enrolments').replaceChildren();
  for (const enrolment of student.enrolments) {
    const row=document.createElement('p');
    const label=document.createElement('span'); label.textContent=enrolment.course.replace('DEMO','Course') + ' · section ' + enrolment.section;
    const value=document.createElement('strong'); value.textContent=enrolment.attendance === null ? 'Attendance missing' : enrolment.attendance + '%';
    row.append(label,value); $('#case-enrolments').append(row);
  }
  if (!student.enrolments.length) $('#case-enrolments').textContent='No course records to check.';
  $('#check-result').replaceChildren();
  const heading=document.createElement('h2'); heading.textContent='Ready to check';
  const hint=document.createElement('p'); hint.textContent='Run the rule to see which conditions pass.';
  $('#check-result').append(heading,hint); $('#check-result').className='';
  $('#open-case-queue').hidden=true;
}
$('#run-check').addEventListener('click', () => {
  const result=LetterkeepEligibility.check(currentCase);
  $('#check-result').replaceChildren();
  const heading=document.createElement('h2'); heading.textContent=result.eligible?'Eligible for a reference':'Not eligible yet';
  const detail=document.createElement('p'); detail.textContent=[['Roster match',result.inRoster],['Grade',result.gradeOK],['Every enrolment’s attendance',result.attendanceOK]].map(([label,ok])=>label + ': ' + (ok?'passes':'does not pass')).join(' · ');
  $('#check-result').append(heading,detail); $('#check-result').className=result.eligible?'passes':'fails';
  $('#open-case-queue').hidden=!result.eligible;
});
$('#open-case-queue').addEventListener('click', () => {
  selected=students.find(student=>student.number===currentCase.number);
  if (!selected) return;
  folder=selected.written?'written':'waiting'; showWorkspace(false); render(); $('#notes').focus({preventScroll:true});
});
render();
fetch('cases.json').then(response => { if (!response.ok) throw new Error('Case file could not be loaded'); return response.json(); }).then(cases => {
  for (const student of cases) {
    const button=document.createElement('button'); button.className='student-row'; button.dataset.case=student.id;
    const name=document.createElement('strong'); name.textContent=student.name;
    const description=document.createElement('small'); description.textContent=student.description;
    button.append(name,description); button.addEventListener('click',()=>chooseCase(student)); $('#case-list').append(button);
  }
  chooseCase(cases[0]); $('#run-check').disabled=false; document.documentElement.dataset.ready='true';
}).catch(error => { $('#check-result').textContent=error.message; $('#run-check').disabled=true; });
