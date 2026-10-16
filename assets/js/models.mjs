/* ThinFilmBook simulator implementations are MIT-licensed. Educational prose and artwork remain separately scoped under CC BY 4.0. See LICENSE.md and LICENSE-MIT. */

const finite = (name, value, low, high) => {
  if (!Number.isFinite(value) || value < low || value > high) {
    throw new RangeError(`${name} must be in [${low}, ${high}]`);
  }
};

const integer = (name, value, low, high) => {
  finite(name, value, low, high);
  if (!Number.isInteger(value)) throw new RangeError(`${name} must be an integer`);
};

/**
 * Idealized steady 1-D feature profile with a first-order wall sink.
 * x is normalized from the opening (0) to the closed end (1); phi is a
 * dimensionless transport-to-reaction parameter, not a process setting.
 */
export function calculateAldProfile({ phi = 1, dose = 1, samples = 51 } = {}) {
  finite('phi', phi, 0, 8);
  finite('dose', dose, 0, 10);
  integer('samples', samples, 11, 201);
  const denominator = Math.cosh(phi);
  const profile = Array.from({ length: samples }, (_, index) => {
    const x = index / (samples - 1);
    const concentrationRatio = Math.cosh(phi * (1 - x)) / denominator;
    const idealizedCoverage = -Math.expm1(-dose * concentrationRatio);
    return { x, concentrationRatio, idealizedCoverage };
  });
  const bottom = profile.at(-1);
  const top = profile[0];
  const conformalityPercent = dose === 0
    ? null
    : top.idealizedCoverage === 0 || bottom.idealizedCoverage === 0
      ? 100 * bottom.concentrationRatio
      : 100 * bottom.idealizedCoverage / top.idealizedCoverage;
  return {
    profile,
    bottomConcentrationRatio: bottom.concentrationRatio,
    bottomCoverage: bottom.idealizedCoverage,
    topCoverage: top.idealizedCoverage,
    conformalityPercent
  };
}

/**
 * Steady series-resistance CVD illustration: gas-film transfer in series with
 * a first-order surface sink. km and ks are m/s; concentration is mol/m^3.
 */
export function calculateCvdFlux({ concentration = 1, massTransfer = 0.1, surfaceReaction = 0.1 } = {}) {
  finite('concentration', concentration, 0, 1e6);
  finite('massTransfer', massTransfer, 1e-9, 1e4);
  finite('surfaceReaction', surfaceReaction, 1e-9, 1e4);
  const totalResistance = 1 / massTransfer + 1 / surfaceReaction;
  return {
    flux: concentration / totalResistance,
    overallVelocity: 1 / totalResistance,
    gasTransferFraction: (1 / massTransfer) / totalResistance,
    surfaceReactionFraction: (1 / surfaceReaction) / totalResistance
  };
}

/**
 * Isotropic Stoney-equation estimate. Inputs are user-selected hypothetical
 * elastic and geometric values; output stress is signed under the declared
 * curvature convention and is not a material/process calibration.
 */
export function calculateStoneyStress({
  substrateModulusGPa = 180,
  poissonRatio = 0.28,
  substrateThicknessUm = 500,
  filmThicknessNm = 100,
  curvatureChangePerM = 0.1
} = {}) {
  finite('substrateModulusGPa', substrateModulusGPa, 1, 1000);
  finite('poissonRatio', poissonRatio, 0, 0.49);
  finite('substrateThicknessUm', substrateThicknessUm, 1, 10000);
  finite('filmThicknessNm', filmThicknessNm, 0.1, 100000);
  finite('curvatureChangePerM', curvatureChangePerM, -1e6, 1e6);
  const biaxialModulusPa = substrateModulusGPa * 1e9 / (1 - poissonRatio);
  const substrateThicknessM = substrateThicknessUm * 1e-6;
  const filmThicknessM = filmThicknessNm * 1e-9;
  const stressPa = biaxialModulusPa * substrateThicknessM ** 2
    * curvatureChangePerM / (6 * filmThicknessM);
  const filmToSubstrateRatio = filmThicknessM / substrateThicknessM;
  const curvatureThicknessProduct = Math.abs(curvatureChangePerM * substrateThicknessM);
  const assumptionWarnings = [];
  if (filmToSubstrateRatio > 0.01) assumptionWarnings.push('film-thickness-ratio');
  if (curvatureThicknessProduct > 0.1) assumptionWarnings.push('curvature-screen');
  return {
    stressMPa: stressPa / 1e6,
    biaxialModulusGPa: biaxialModulusPa / 1e9,
    filmToSubstrateRatio,
    curvatureThicknessProduct,
    assumptionWarnings
  };
}
