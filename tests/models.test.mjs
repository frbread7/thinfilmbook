import test from 'node:test';
import assert from 'node:assert/strict';
import { calculateAldProfile, calculateCvdFlux, calculateStoneyStress } from '../assets/js/models.mjs';

test('ALD profile is uniform without a sink and attenuates with transport limitation', () => {
  const uniform = calculateAldProfile({ phi: 0, dose: 1 });
  assert.equal(uniform.bottomConcentrationRatio, 1);
  assert.equal(uniform.conformalityPercent, 100);
  const limited = calculateAldProfile({ phi: 3, dose: 1 });
  assert.ok(limited.bottomConcentrationRatio < 0.1);
  assert.ok(limited.bottomCoverage < limited.topCoverage);
  assert.equal(limited.profile.length, 51);
  const tiny = calculateAldProfile({ phi: 5, dose: 1e-30 });
  assert.ok(Number.isFinite(tiny.conformalityPercent));
  assert.ok(Math.abs(tiny.conformalityPercent - 100 * tiny.bottomConcentrationRatio) < 1e-10);
  const subnormal = calculateAldProfile({ phi: 5, dose: Number.MIN_VALUE });
  assert.ok(Number.isFinite(subnormal.conformalityPercent));
});

test('ALD input bounds reject invalid dimensionless values', () => {
  assert.throws(() => calculateAldProfile({ phi: -1 }), RangeError);
  assert.throws(() => calculateAldProfile({ samples: 2 }), RangeError);
  assert.equal(calculateAldProfile({ dose: 0 }).conformalityPercent, null);
});

test('CVD series resistance transitions from reaction to transport limitation', () => {
  const reactionLimited = calculateCvdFlux({ massTransfer: 0.1, surfaceReaction: 0.001 });
  const transportLimited = calculateCvdFlux({ massTransfer: 0.001, surfaceReaction: 0.1 });
  assert.ok(Math.abs(reactionLimited.flux - 0.001 / (1 + 0.01)) < 1e-12);
  assert.ok(reactionLimited.surfaceReactionFraction > reactionLimited.gasTransferFraction);
  assert.ok(transportLimited.gasTransferFraction > transportLimited.surfaceReactionFraction);
});

test('Stoney estimate has correct unit scaling and signed response', () => {
  const baseline = calculateStoneyStress({ curvatureChangePerM: 0.1 });
  assert.ok(baseline.stressMPa > 0);
  assert.deepEqual(baseline.assumptionWarnings, []);
  const chapterReference = calculateStoneyStress({
    substrateModulusGPa: 130,
    poissonRatio: 0.28,
    substrateThicknessUm: 500,
    filmThicknessNm: 1000,
    curvatureChangePerM: 0.01
  });
  assert.ok(Math.abs(chapterReference.stressMPa - 75) < 0.5);
  assert.equal(calculateStoneyStress({ curvatureChangePerM: -0.1 }).stressMPa, -baseline.stressMPa);
  const doubledFilm = calculateStoneyStress({ filmThicknessNm: 200, curvatureChangePerM: 0.1 });
  assert.ok(Math.abs(doubledFilm.stressMPa * 2 - baseline.stressMPa) < 1e-10);
  const outsideApproximation = calculateStoneyStress({ substrateThicknessUm: 1, filmThicknessNm: 100000, curvatureChangePerM: 1e6 });
  assert.deepEqual(outsideApproximation.assumptionWarnings, ['film-thickness-ratio', 'curvature-screen']);
});

test('all models reject non-finite or out-of-range inputs', () => {
  assert.throws(() => calculateCvdFlux({ concentration: Number.NaN }), RangeError);
  assert.throws(() => calculateStoneyStress({ poissonRatio: 0.5 }), RangeError);
});
