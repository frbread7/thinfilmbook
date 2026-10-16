import assert from 'node:assert/strict';
import { test } from 'node:test';

class Element {
  constructor(value = '') {
    this.value = value;
    this.textContent = '';
    this.attributes = {};
    this.children = [];
    this.listeners = new Map();
  }

  addEventListener(type, listener) {
    this.listeners.set(type, listener);
  }

  click() {
    this.listeners.get('click')?.();
  }

  append(node) {
    this.children.push(node);
  }

  removeChild(node) {
    const index = this.children.indexOf(node);
    if (index >= 0) this.children.splice(index, 1);
  }

  get firstChild() {
    return this.children[0] ?? null;
  }

  setAttribute(name, value) {
    this.attributes[name] = value;
  }
}

function installDocument(lang) {
  const elements = new Map(Object.entries({
    'ald-phi': new Element('1.5'),
    'ald-dose': new Element('1'),
    'ald-chart': new Element(),
    'result-ald-conformality': new Element(),
    'run-ald': new Element(),
    'cvd-concentration': new Element('1'),
    'cvd-km': new Element('0.1'),
    'cvd-ks': new Element('0.1'),
    'result-cvd-resistances': new Element(),
    'run-cvd': new Element(),
    'stoney-modulus': new Element('180'),
    'stoney-poisson': new Element('0.28'),
    'stoney-substrate': new Element('500'),
    'stoney-film': new Element('100'),
    'stoney-curvature': new Element('0.1'),
    'result-stoney-stress': new Element(),
    'run-stoney': new Element(),
  }));
  globalThis.document = {
    documentElement: { lang },
    getElementById: id => elements.get(id) ?? null,
    createElementNS: (_namespace, _tag) => new Element(),
  };
  return elements;
}

test('application handlers render model results and localized validation errors', async () => {
  try {
    const english = installDocument('en');
    await import('../assets/js/site.js?handler-test-en');
    assert.match(english.get('result-ald-conformality').textContent, /Bottom concentration C\/C₀: [\d.]+/);
    assert.match(english.get('result-cvd-resistances').textContent, /Molar flux: [\d.e+-]+/);
    assert.match(english.get('result-stoney-stress').textContent, /Estimated average film stress: [\d.e+-]+ MPa/);
    assert.ok(english.get('ald-chart').children.length > 0, 'ALD handler should draw the profile');

    english.get('ald-dose').value = '';
    english.get('run-ald').click();
    assert.match(english.get('result-ald-conformality').textContent, /Enter a value before running the model/);
    english.get('ald-dose').value = '1';
    english.get('ald-phi').value = '9';
    english.get('run-ald').click();
    assert.match(english.get('result-ald-conformality').textContent, /Check the input ranges and try again/);
    english.get('cvd-concentration').value = '-1';
    english.get('run-cvd').click();
    assert.match(english.get('result-cvd-resistances').textContent, /Check the input ranges and try again/);
    english.get('stoney-modulus').value = '0';
    english.get('run-stoney').click();
    assert.match(english.get('result-stoney-stress').textContent, /Check the input ranges and try again/);

    const korean = installDocument('ko');
    await import('../assets/js/site.js?handler-test-ko');
    assert.match(korean.get('result-ald-conformality').textContent, /하단 농도 C\/C₀: [\d.]+/);
    assert.match(korean.get('result-cvd-resistances').textContent, /몰 플럭스: [\d.e+-]+/);
    assert.match(korean.get('result-stoney-stress').textContent, /추정 평균 막 응력: [\d.e+-]+ MPa/);
    assert.ok(korean.get('ald-chart').children.length > 0, 'Korean ALD handler should draw the profile');
    korean.get('ald-dose').value = '';
    korean.get('run-ald').click();
    assert.match(korean.get('result-ald-conformality').textContent, /모델을 실행하기 전에 값을 입력하세요/);
    korean.get('cvd-concentration').value = '-1';
    korean.get('run-cvd').click();
    assert.match(korean.get('result-cvd-resistances').textContent, /입력 범위를 확인하고 다시 실행하세요/);
  } finally {
    delete globalThis.document;
  }
});
