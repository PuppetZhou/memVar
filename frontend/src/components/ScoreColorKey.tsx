import './score-color-key.css';
import { sequenceScoreGradient, sequenceScoreStops, type SequenceScoreScale } from '../lib/palette';

export function ScoreGradient({ id, bottom, top, scale }: { id: string; bottom: number; top: number; scale: SequenceScoreScale }) {
  return <defs><linearGradient id={id} gradientUnits="userSpaceOnUse" x1="0" x2="0" y1={bottom} y2={top}>
    {sequenceScoreStops[scale].map((color, i) => <stop key={color} offset={i / (sequenceScoreStops[scale].length - 1)} stopColor={color}/>) }
  </linearGradient></defs>;
}

export function ScoreColorKey({ compact = false, scale }: { compact?: boolean; scale: SequenceScoreScale }) {
  return <span className={`score-color-key${compact ? ' is-compact' : ''}`} aria-label="Continuous score colour scale, 0 to 1">
    <i style={{ background: sequenceScoreGradient(scale) }}/>
    <span>{(compact ? [0, 1] : [0, .25, .5, .75, 1]).map(value => <small key={value}>{value}</small>)}</span>
  </span>;
}
