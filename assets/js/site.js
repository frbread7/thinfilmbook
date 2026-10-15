import { calculateAldProfile, calculateCvdFlux, calculateStoneyStress } from './models.mjs';

const locale = document.documentElement.lang === 'ko' ? 'ko' : 'en';
const undefinedCoverage = {
  en: 'Coverage ratio is undefined at zero exposure.',
  ko: '노출량이 0이면 피복률 비는 정의되지 않습니다.'
}[locale];
const requiredValueMessage = {
  en: 'Enter a value before running the model.',
  ko: '모델을 실행하기 전에 값을 입력하세요.'
}[locale];
const message = {
  en: {
    error: 'Check the input ranges and try again.',
    ald: (result) => result.conformalityPercent === null
      ? `Bottom concentration C/C₀: ${format(result.bottomConcentrationRatio)}. ${undefinedCoverage}`
      : `Bottom concentration C/C₀: ${format(result.bottomConcentrationRatio)}; bottom/top idealized coverage: ${format(result.conformalityPercent)}%.`,
    cvd: (result) => `Molar flux: ${format(result.flux)} mol/m²/s; overall velocity: ${format(result.overallVelocity)} m/s. Larger resistance: ${result.gasTransferFraction >= result.surfaceReactionFraction ? 'gas-film mass transfer' : 'surface reaction'}.`,
    stress: (result) => {
      const warnings = [];
      if (result.assumptionWarnings.includes('film-thickness-ratio')) warnings.push(`Film/substrate thickness ratio ${format(100 * result.filmToSubstrateRatio)}% exceeds the 1% screening threshold for this thin-film approximation.`);
      if (result.assumptionWarnings.includes('curvature-screen')) warnings.push(`|Δκ|tₛ = ${format(result.curvatureThicknessProduct)} exceeds the 0.1 small-curvature screening threshold.`);
      return `Estimated average film stress: ${format(result.stressMPa)} MPa (substrate biaxial modulus ${format(result.biaxialModulusGPa)} GPa).${warnings.length ? ` Warning: ${warnings.join(' ')}` : ''}`;
    },
  },
  ko: {
    error: '입력 범위를 확인하고 다시 실행하세요.',
    ald: (result) => result.conformalityPercent === null
      ? `하단 농도 C/C₀: ${format(result.bottomConcentrationRatio)}. ${undefinedCoverage}`
      : `하단 농도 C/C₀: ${format(result.bottomConcentrationRatio)}; 하단/상단 이상화 피복률: ${format(result.conformalityPercent)}%.`,
    cvd: (result) => `몰 플럭스: ${format(result.flux)} mol/m²/s; 전체 속도 계수: ${format(result.overallVelocity)} m/s. 더 큰 저항: ${result.gasTransferFraction >= result.surfaceReactionFraction ? '기체막 물질 전달' : '표면 반응'}.`,
    stress: (result) => {
      const warnings = [];
      if (result.assumptionWarnings.includes('film-thickness-ratio')) warnings.push(`막/기판 두께비 ${format(100 * result.filmToSubstrateRatio)}%가 이 박막 근사의 1% 검토 기준을 넘었습니다.`);
      if (result.assumptionWarnings.includes('curvature-screen')) warnings.push(`|Δκ|tₛ = ${format(result.curvatureThicknessProduct)}가 작은 곡률의 0.1 검토 기준을 넘었습니다.`);
      return `추정 평균 막 응력: ${format(result.stressMPa)} MPa (기판 등축 탄성률 ${format(result.biaxialModulusGPa)} GPa).${warnings.length ? ` 주의: ${warnings.join(' ')}` : ''}`;
    },
  }
}[locale];

function format(value) {
  return Number(value).toPrecision(4).replace(/\.0+(e|$)/, '$1');
}

function readValue(id) {
  const input = document.getElementById(id);
  if (!input) throw new Error(`Missing model input: ${id}`);
  if (input.value.trim() === '') throw new RangeError(requiredValueMessage);
  const value = Number(input.value);
  if (!Number.isFinite(value)) throw new RangeError(`Invalid number for ${id}`);
  return value;
}

function show(id, text) {
  const output = document.getElementById(id);
  if (output) output.textContent = text;
}

function drawProfile(svg, profile) {
  if (!svg) return;
  const NS = 'http://www.w3.org/2000/svg';
  const left = 48, right = 700, top = 24, bottom = 216;
  while (svg.firstChild) svg.removeChild(svg.firstChild);
  for (let tick = 0; tick <= 4; tick += 1) {
    const y = bottom - tick * (bottom - top) / 4;
    const line = document.createElementNS(NS, 'line');
    line.setAttribute('x1', String(left)); line.setAttribute('x2', String(right));
    line.setAttribute('y1', String(y)); line.setAttribute('y2', String(y));
    line.setAttribute('class', tick === 0 ? 'chart-axis' : 'chart-grid');
    svg.append(line);
  }
  for (const item of [
    { key: 'concentrationRatio', className: 'chart-line concentration' },
    { key: 'idealizedCoverage', className: 'chart-line coverage' }
  ]) {
    const points = profile.map((point) => {
      const x = left + point.x * (right - left);
      const y = bottom - point[item.key] * (bottom - top);
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    }).join(' ');
    const line = document.createElementNS(NS, 'polyline');
    line.setAttribute('points', points);
    line.setAttribute('class', item.className);
    svg.append(line);
  }
  const label = (x, y, text) => {
    const node = document.createElementNS(NS, 'text');
    node.setAttribute('x', String(x)); node.setAttribute('y', String(y));
    node.setAttribute('class', 'chart-label'); node.textContent = text;
    svg.append(node);
  };
  label(left, 244, locale === 'ko' ? '입구' : 'Opening');
  label(right - 34, 244, locale === 'ko' ? '하단' : 'Bottom');
  label(left, 16, 'C/C₀, θ');
}

function runAld() {
  try {
    const result = calculateAldProfile({ phi: readValue('ald-phi'), dose: readValue('ald-dose') });
    drawProfile(document.getElementById('ald-chart'), result.profile);
    show('result-ald-conformality', message.ald(result));
  } catch (error) {
    show('result-ald-conformality', `${message.error} ${error.message}`);
  }
}

function runCvd() {
  try {
    const result = calculateCvdFlux({
      concentration: readValue('cvd-concentration'),
      massTransfer: readValue('cvd-km'),
      surfaceReaction: readValue('cvd-ks')
    });
    show('result-cvd-resistances', message.cvd(result));
  } catch (error) {
    show('result-cvd-resistances', `${message.error} ${error.message}`);
  }
}

function runStoney() {
  try {
    const result = calculateStoneyStress({
      substrateModulusGPa: readValue('stoney-modulus'),
      poissonRatio: readValue('stoney-poisson'),
      substrateThicknessUm: readValue('stoney-substrate'),
      filmThicknessNm: readValue('stoney-film'),
      curvatureChangePerM: readValue('stoney-curvature')
    });
    show('result-stoney-stress', message.stress(result));
  } catch (error) {
    show('result-stoney-stress', `${message.error} ${error.message}`);
  }
}

document.getElementById('run-ald')?.addEventListener('click', runAld);
document.getElementById('run-cvd')?.addEventListener('click', runCvd);
document.getElementById('run-stoney')?.addEventListener('click', runStoney);

runAld();
runCvd();
runStoney();
