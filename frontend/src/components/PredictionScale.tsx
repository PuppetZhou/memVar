import { number } from '../api';
import { interpolateColor } from '../lib/palette';
import { PREDICTOR_GUIDES } from './predictor-guides';
import './prediction-scale.css';

// A native-score axis, not a calibrated probability or a cross-tool ranking.
export function predictionDirection(field: string) {
  const direction = PREDICTOR_GUIDES[field]?.direction ?? '';
  const effect = /more predicted (effect|impact)/.test(direction);
  return { direction, effect, lower: direction.startsWith('Lower') };
}
export function PredictionDirection({ field }: { field: string }) {
  const { direction, effect, lower } = predictionDirection(field);
  return <span className={effect ? 'prediction-direction-chip' : 'vc-predictor-direction'} title={direction}>
    {effect ? `${lower ? '↓ Lower' : '↑ Higher'} = more ${direction.includes('impact') ? 'impact' : 'effect'}` : direction}
  </span>;
}
export function PredictionScale({ field, value }: { field: string; value: number }) {
  const { effect, lower } = predictionDirection(field);
  if (!effect || PREDICTOR_GUIDES[field]?.scale !== '0–1' || !Number.isFinite(value) || value < 0 || value > 1) return null;
  return <div className="prediction-native-scale" role="img" aria-label={`Native score ${value} on 0 to 1 scale; ${lower ? 'lower' : 'higher'} scores indicate more predicted effect`}>
    <span>0</span><i style={{ background: `linear-gradient(to right, ${lower ? '#c73748, #f0e5e8, #2774ac' : '#2774ac, #f0e5e8, #c73748'})` }}><b style={{ left: `${value * 100}%` }}/></i><span>1</span>
  </div>;
}

export function PredictionRank({ field, value }: { field: string; value: number }) {
  if (!['CADD_phred', 'alphagenome_avi_phred'].includes(field) || !Number.isFinite(value) || value < 0) return null;
  const top = 100 * Math.pow(10, -value / 10);
  // Fixed display axis only; 40 is not a classification threshold or a maximum score.
  const progress = Math.min(1, value / 40);
  const color = interpolateColor('#2774ac', '#c73748', progress);
  return <div className="prediction-rank-note" title="Approximate upper-tail rank in this predictor’s reference distribution, not disease probability. Bar: native PHRED 0–40; scores ≥40 use the endpoint. No classification cutoff.">
    <b>Top {top < 0.01 ? top.toExponential(1) : number(top, 2)}%</b>
    <div className="prediction-native-scale prediction-rank-scale" role="img" aria-label={`PHRED ${value}; display axis 0 to 40 or above`}>
      <span>0</span><i><em style={{ width: `${progress * 100}%`, background: color }}/><b style={{ left: `${progress * 100}%`, background: color }}/></i><span>40+</span>
    </div>
    <span>reference rank</span>
  </div>;
}
