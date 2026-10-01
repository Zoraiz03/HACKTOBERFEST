'use strict';
const $ = (id) => document.getElementById(id);
let finalSkill = null;
let skillMarkdown = '';
let busy = false;
const meetingWorkflow = 'Read meeting notes and extract decisions, action items, owners, and deadlines.';

function message(id, text) {
  $(id).textContent = text;
  $(id).hidden = !text;
}
function setBusy(value) {
  busy = value;
  for (const id of ['generate', 'run', 'meeting-example', 'generated-example']) $(id).disabled = value;
  $('workflow').disabled = value;
  $('sample-input').disabled = value;
}
async function post(path, body) {
  let response;
  try {
    response = await fetch(path, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
  } catch {
    throw new Error('Cannot reach SkillSmith. Check that the local server is running and try again.');
  }
  let data;
  try { data = await response.json(); }
  catch { throw new Error('The server returned an unexpected response. Please try again.'); }
  if (!response.ok) {
    const detail = data.detail;
    throw new Error(typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map(e => e.msg).join('\n') : `Request failed (${response.status}). Please try again.`);
  }
  return data;
}
function element(tag, text, className) {
  const node = document.createElement(tag);
  node.textContent = text;
  if (className) node.className = className;
  return node;
}
function showPipeline(data) {
  $('pipeline-section').hidden = false;
  const pipeline = $('pipeline');
  const history = $('repair-history');
  pipeline.replaceChildren();
  history.replaceChildren();
  const attempts = data.repair_attempts || [];
  const stages = ['✓ Generated', data.initial_valid ? '✓ Validated' : '⚠ Validation issue detected'];
  if (attempts.length) stages.push(data.final_valid ? `✓ Repaired (${attempts.length} ${attempts.length === 1 ? 'attempt' : 'attempts'})` : `⚠ ${attempts.length} repair attempts`);
  stages.push(data.final_valid ? '✓ Skill Ready' : '✕ Validation failed');
  stages.forEach((text, index) => {
    if (index) pipeline.append(element('span', '→', 'arrow'));
    pipeline.append(element('span', text, `node${text.startsWith('✕') || text.startsWith('⚠') ? ' failed' : ''}`));
  });
  for (const attempt of attempts) {
    const card = element('div', '', 'repair');
    card.append(element('strong', `AI Repair #${attempt.attempt}`));
    for (const error of attempt.errors_before || []) card.append(element('p', `${error.field}: ${error.message}`));
    const fields = [...new Set((attempt.errors_before || []).map(e => e.field))];
    for (const field of fields) {
      const before = attempt.before?.[field];
      const after = attempt.after?.[field];
      if (typeof before === 'string') card.append(element('pre', `${field}: ${before || '(empty)'}\n↓\n${typeof after === 'string' ? after || '(empty)' : 'No valid structured response'}`));
    }
    card.append(element('p', attempt.valid_after ? '✓ Deterministic validation passed' : '⚠ Validation still failed'));
    history.append(card);
  }
  if (data.initial_valid) history.append(element('p', '✓ Passed validation on first attempt · Deterministic validation passed', 'validation-note'));
  if (!data.final_valid) {
    const errors = data.final_validation?.errors || [];
    history.append(element('p', `Skill is not ready to run. ${errors.map(e => `${e.field}: ${e.message}`).join(' ')} Try describing the workflow again.`, 'error'));
  }
}
$('meeting-example').addEventListener('click', () => {
  $('workflow').value = meetingWorkflow;
  $('workflow').focus();
});
$('generate-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  if (busy) return;
  const workflow = $('workflow').value.trim();
  if (workflow.length < 10) { message('generation-error', 'Describe your workflow using at least 10 characters.'); return; }
  finalSkill = null;
  skillMarkdown = '';
  for (const id of ['pipeline-section', 'skill-section', 'test-section', 'result-section']) $(id).hidden = true;
  for (const id of ['generation-error', 'run-error', 'run-status', 'copy-status']) message(id, '');
  $('sample-input').value = '';
  $('output').textContent = '';
  setBusy(true);
  $('generate').textContent = 'Generating…';
  message('generation-status', 'Generating with local AI...');
  try {
    const data = await post('/api/generate-and-repair', {workflow});
    showPipeline(data);
    if (data.final_valid && data.final_skill && data.skill_md) {
      finalSkill = data.final_skill;
      skillMarkdown = data.skill_md;
      $('skill-name').textContent = finalSkill.name;
      $('skill-description').textContent = finalSkill.description;
      $('skill-md').textContent = skillMarkdown;
      $('skill-section').hidden = false;
      $('test-section').hidden = false;
      $('generated-example').hidden = !finalSkill.example?.input;
      message('generation-status', 'Your skill is ready. Test it with sample input below.');
    } else message('generation-status', 'Generation finished. Review the validation issues below.');
  } catch (error) {
    message('generation-status', '');
    message('generation-error', error.message);
  } finally {
    setBusy(false);
    $('generate').textContent = 'Generate Agent Skill →';
  }
});
$('generated-example').addEventListener('click', () => {
  if (finalSkill?.example?.input) $('sample-input').value = finalSkill.example.input;
  $('sample-input').focus();
});
$('run-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  if (busy || !finalSkill) return;
  const input = $('sample-input').value.trim();
  if (!input) { message('run-error', 'Paste sample input before running the skill.'); return; }
  message('run-error', '');
  message('copy-status', '');
  $('result-section').hidden = true;
  $('output').textContent = '';
  setBusy(true);
  $('run').textContent = 'Running…';
  message('run-status', 'Running skill locally...');
  try {
    const data = await post('/api/run', {skill: finalSkill, input});
    $('output').textContent = data.output;
    $('result-section').hidden = false;
    message('run-status', '✓ Execution complete');
  } catch (error) {
    message('run-status', '');
    message('run-error', error.message);
  } finally {
    setBusy(false);
    $('run').textContent = 'Run Skill →';
  }
});
async function copy(text, label) {
  try {
    await navigator.clipboard.writeText(text);
    message('copy-status', `${label} copied to clipboard.`);
  } catch {
    message('copy-status', 'Clipboard unavailable. Select the text in the panel and copy it manually.');
  }
}
$('copy-skill').addEventListener('click', () => copy(skillMarkdown, 'SKILL.md'));
$('copy-output').addEventListener('click', () => copy($('output').textContent, 'Output'));

const downloadSkill = element('button', 'Download SKILL.md', 'button compact');
downloadSkill.type = 'button';
$('copy-skill').after(downloadSkill);
downloadSkill.addEventListener('click', () => {
  if (!skillMarkdown) return;
  const blob = new Blob([skillMarkdown], {type: 'text/markdown;charset=utf-8'});
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'SKILL.md';
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
