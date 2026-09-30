/** dbNSFP 5.4a source dictionary, reviewed 2026-09-30.
 * These marks explain source scores; they never generate source calls.
 * Reported ranges are plotting context, not theoretical score limits.
 */
export type ScoreReference = { range?: [number, number]; marks: number[]; note: string; lower?: boolean; conservation?: boolean };
export const SCORE_REFERENCES: Record<string, ScoreReference> = {
  ESM1b_score: { range: [-24.538, 6.937], marks: [-7.5, 0], lower: true, note: '−7.5: source test-set D/T reference, not a universal cutoff. 0: equal model preference.' },
  PROVEAN_score: { range: [-14, 14], marks: [-2.5], lower: true, note: 'Source rule: ≤−2.5 damaging; >−2.5 neutral.' },
  BayesDel_addAF_score: { range: [-1.11707, .750927], marks: [.0692655], note: 'Author-suggested D/T reference: 0.0692655, with MaxAF.' },
  BayesDel_noAF_score: { range: [-1.31914, .840878], marks: [-.0570105], note: 'Author-suggested D/T reference: −0.0570105, without MaxAF.' },
  MetaSVM_score: { range: [-2, 3], marks: [0], note: 'Source D/T boundary: 0; higher scores favor damaging.' },
  MutationAssessor_score: { range: [-5.17, 6.49], marks: [.8, 1.935, 3.5], note: 'Functional-impact boundaries: 0.8 neutral/low, 1.935 low/medium, 3.5 medium/high.' },
  GPN_MSA_score: { range: [-14.21, 12.87], marks: [-7], lower: true, note: 'dbNSFP source rule: <−7 damaging; otherwise tolerated.' },
  popEVE_score: { marks: [-5.056, -4.617], lower: true, note: 'Source model bands: <−5.056 severe; −5.056 to <−4.617 moderate; ≥−4.617 benign. Not clinical assertions.' },
  MPC_score: { range: [0, 5], marks: [], note: 'Source range 0–5; no universal binary cutoff supplied.' },
  'VARITY_R_LOO_score': { range: [0, 1], marks: [], note: 'Same native 0–1 score as VARITY R; leave-one-variant-out evaluation. No universal cutoff.' },
  'VARITY_ER_LOO_score': { range: [0, 1], marks: [], note: 'Same native 0–1 score as VARITY ER; leave-one-variant-out evaluation. No universal cutoff.' },
  'GERP++_RS': { range: [-12.3, 6.17], marks: [], conservation: true, note: 'Source range; higher indicates greater conservation, not pathogenicity.' },
  bStatistic: { range: [0, 1000], marks: [0, 1000], conservation: true, lower: true, note: '0: strong loss of neutral diversity; 1000: little background selection.' },
  MisFit_S_score: { range: [0, .5], marks: [.0001], conservation: true, note: '<0.0001: source noise reference. No fixed pathogenicity cutoff; interpretation depends on gene and age of onset.' },
};
