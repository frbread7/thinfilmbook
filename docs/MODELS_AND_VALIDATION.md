# Models and validation

All three labs use inputs chosen by the reader. The numerical values shown on first load are illustrative defaults. The labs are local browser calculations: they do not call an external API, store inputs, or contact process equipment.

## ALD feature profile

The explorer uses a steady one-dimensional diffusion-reaction profile in a normalized feature, with the opening at `x = 0` and a closed end at `x = 1`:

`C(x)/C₀ = cosh(φ(1 − x)) / cosh(φ)`

Here `φ` is a dimensionless transport-to-reaction parameter. An idealized single exposure maps local concentration to coverage by `θ(x) = 1 − exp(−D C(x)/C₀)`, where `D` is a dimensionless exposure. The bottom/top coverage ratio is undefined when `D = 0` and is reported as such. Inputs are bounded to `0 ≤ φ ≤ 8` and `0 ≤ D ≤ 10`.

This is a steady first-order wall-sink illustration. It omits feature evolution, transient precursor pulses, surface-site chemistry, parasitic reactions, by-products, loading, and cycle-to-cycle effects. It is not a cycle-accurate ALD simulator and cannot select process conditions.

## CVD series resistance

For bulk concentration `C_b` in mol/m³, gas-film mass-transfer coefficient `k_m` in m/s, and first-order surface-reaction coefficient `k_s` in m/s:

`J = C_b / (1/k_m + 1/k_s)`

The denominator has units s/m, so the flux `J` has units mol/(m²·s). The model assumes steady one-dimensional transfer, constant coefficients, one limiting reactant, and a linear surface sink. It does not model reactor geometry, gas-phase chemistry, depletion, thermal gradients, or wafer-scale uniformity.

## Stoney stress estimate

For an isotropic substrate with Young's modulus `E_s`, Poisson ratio `ν_s`, substrate thickness `t_s`, film thickness `t_f`, and curvature change `Δκ`:

`σ_f = [E_s/(1 − ν_s)] t_s² Δκ / (6 t_f)`

The implementation accepts modulus in GPa, substrate thickness in µm, film thickness in nm, and curvature change in m⁻¹, then reports MPa. The sign follows the selected curvature convention; it is not a universal tensile/compressive label. The approximation assumes a thin uniform film on a much thicker elastic substrate, small curvature, and an equibiaxial average stress. Silicon's elastic anisotropy means this isotropic estimate must not be treated as a wafer-specific calibration.

The lab displays screening warnings when the film/substrate thickness ratio exceeds 1% or when `|Δκ| t_s` exceeds 0.1. These are conservative educational prompts for the assumptions above, not universal accuracy bounds or proof that an estimate below either threshold is valid for a particular material system.

## Verification evidence

`tests/models.test.mjs` checks limiting behavior, unit scaling, sign response, and rejected inputs. `tests/test_site.py` checks bilingual source structure, emitted routes, citations, language links, and each declared lab anchor. The browser-only interactions are exercised with local Playwright during candidate verification; browser output is not deployment evidence.
