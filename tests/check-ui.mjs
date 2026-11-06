import assert from 'node:assert/strict';
import {browserPage} from './browser.mjs';
const page=await browserPage(process.argv[2] || 'http://127.0.0.1:8765/letterkeep/');
const e=page.evaluate;
try {
  for(const [id,passes] of [['alice',true],['one-course',false],['missing',false],['low-grade',false],['no-match',false]]) {
    await e("document.querySelector('[data-case=\""+id+"\"]').click();document.querySelector('#run-check').click()");
    assert.equal(await e("document.querySelector('#check-result').className"),passes?'passes':'fails',id);
    assert.equal(await e("document.querySelector('#open-case-queue').hidden"),!passes,id+' queue access');
  }
  await e("document.querySelector('[data-case=\"one-course\"]').click()");
  assert.match(await e("document.querySelector('#case-enrolments').textContent"),/96%.*60%/s);
  await e("document.querySelector('[data-case=\"missing\"]').click()");
  assert.match(await e("document.querySelector('#case-enrolments').textContent"),/Attendance missing/);
  await e("document.querySelector('[data-case=\"alice\"]').click();document.querySelector('#run-check').click();document.querySelector('#open-case-queue').click()");
  assert.equal(await e("document.activeElement.id"),'notes');
  assert.match(await e("document.querySelector('#evidence-preview').textContent"),/Fictional transcript.*88.5%.*Fictional statement/s);
  await e("document.querySelector('#evidence-preview details').open=true;document.querySelector('[data-prompt]').click()");
  assert.equal(await e("document.querySelector('#evidence-preview details').open"),true,'writing notes preserves the evidence preview');
  assert.match(await e("document.querySelector('#notes').value"),/How I know the student/);
  assert.equal(await e("document.querySelectorAll('.student-meta').length"),0);
  await e("document.querySelector('#notes').value='Observed careful iteration';document.querySelector('#notes').dispatchEvent(new Event('input'));document.querySelectorAll('.student-row')[6].click();document.querySelectorAll('#student-list .student-row')[0].click()");
  assert.equal(await e("document.querySelector('#notes').value"),'Observed careful iteration');
  for(const [w,h] of [[1230,690],[1920,1080]]) {
    await page.size(w,h);
    assert.ok(await e("document.querySelector('#notes').getBoundingClientRect().bottom < innerHeight"),'notes in first screen '+w);
    assert.ok(await e("document.querySelector('#mark-written').getBoundingClientRect().bottom < innerHeight"),'completion in first screen '+w);
  }
  await e("document.querySelector('#mark-written').click()");
  assert.equal(await e("document.querySelector('#written-count').textContent"),'1');
  await e("document.querySelector('#written-folder').click();document.querySelector('#undo').click()");
  assert.equal(await e("document.querySelector('#waiting-count').textContent"),'3');
  await page.size(390,844);
  assert.notEqual(await e("getComputedStyle(document.querySelector('.notes-heading span')).display"),'none');
  assert.match(await e("document.querySelector('.session-note').textContent"),/reset on reload/);
  assert.ok(await e("document.documentElement.scrollWidth <= innerWidth"),'phone fits');
  assert.equal(await e("parseFloat(getComputedStyle(document.querySelector('#notes')).fontSize)"),16,'phone font size unchanged');
  await page.navigate(process.argv[2] || 'http://127.0.0.1:8765/letterkeep/');
  await e("document.querySelector('#queue-view').click()");
  assert.equal(await e("document.querySelector('#notes').value"),'');
  assert.equal(await e("document.querySelector('#waiting-count').textContent"),'3');
  assert.deepEqual(page.errors,[]);
  console.log('PASS: five eligibility cases; evidence; queue connection; notes, completion and undo; reload lifetime; 1230/1920/390 layout.');
} finally {await page.close();}

