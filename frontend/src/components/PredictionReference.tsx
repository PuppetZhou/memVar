import { PREDICTOR_GUIDES } from './predictor-guides';
import { SCORE_REFERENCES } from './predictor-references';
import { interpolateColor } from '../lib/palette';

export default function PredictionReference({ field, value, compact = false }: { field: string; value: number; compact?: boolean }) {
  const guide = PREDICTOR_GUIDES[field], reference = SCORE_REFERENCES[field];
  if (!guide || !Number.isFinite(value) || guide.scale === '0–1' || guide.scale === 'PHRED rank scale') return null;
  if (!reference) return <span className="prediction-reference-note" title={guide.criterion}>No established reference cutoff</span>;
  const anchors = reference.range ?? reference.marks;
  const low = Math.min(value, ...anchors), high = Math.max(value, ...anchors);
  const padding = reference.range ? 0 : Math.max(1, (high - low) * .15);
  const min = low - padding, max = high + padding;
  const position = (v: number) => (v - min) / (max - min || 1) * 100;
  const fraction = position(value) / 100;
  const effect = reference.lower ? 1 - fraction : fraction;
  const color = interpolateColor('#2774ac', reference.conservation ? '#163f68' : '#c73748', effect);
  const background = reference.conservation ? 'linear-gradient(to right,#cde8f4,#2774ac)' : reference.lower ? 'linear-gradient(to right,#c73748,#f0e5e8,#2774ac)' : 'linear-gradient(to right,#2774ac,#f0e5e8,#c73748)';
  return <div className="prediction-reference" title={`${reference.note} ${reference.range ? 'Source-reported plotting range, extended for out-of-range values.' : 'Local display window includes this score and the reference marks.'} Dashed marks: source references. Solid marker: current score.`}>
    <div className="prediction-native-scale" role="img" aria-label={`Score ${value}; references ${reference.marks.join(', ') || 'none'}; axis ${min} to ${max}. ${reference.note}`}>
      <span>{Number(min.toPrecision(3))}</span><i style={{background}}>
        {reference.marks.map(mark => <em className="prediction-reference-tick" key={mark} style={{left:`${position(mark)}%`}}/>)}
        <b style={{left:`${position(value)}%`,background:color}}/>
      </i><span>{Number(max.toPrecision(3))}</span>
    </div>
    <span className="prediction-reference-note">{reference.marks.length ? `Ref ${reference.marks.join(' / ')}` : 'Source range · no cutoff'}</span>
    {!compact&&<details className="prediction-reference-info"><summary>Reference meaning</summary><p>{reference.note}</p><a href="https://dist.genos.us/release/dbNSFP5.4a_variant.columns.txt" target="_blank" rel="noreferrer">dbNSFP 5.4a source definition ↗</a></details>}
  </div>;
}
