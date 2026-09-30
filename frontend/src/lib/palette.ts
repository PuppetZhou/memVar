/** memVar presentation palette. Colours never define scientific categories or thresholds. */
export const palette = {
  blue: '#7b95c6', cyan: '#49c2d9', ice: '#a1d8e8', sage: '#67a583',
  leaf: '#a2c986', mist: '#d0e2c0', butter: '#fded95', peach: '#ffc1a6',
  apricot: '#f59c7c', coral: '#f47254', rose: '#c85e62',
  missing: '#e5e9ef', ink: '#202938', blueInk: '#365982',
} as const;

export const clinicalColors = {
  pathogenic: palette.rose, uncertain: palette.butter, benign: palette.sage,
  conflicting: palette.blue, other: palette.cyan, unclassified: '#c4ccd7',
} as const;

// Scientific fills share the sequence palette. Readable ink is derived from each fill.
export const evidenceInk = {
  damaging: predictionTextColor(palette.rose), tolerated: predictionTextColor(palette.sage),
  uncertain: predictionTextColor(palette.butter),
};
export const predictionPalette = {
  rose: palette.rose, coral: palette.coral, apricot: palette.apricot,
  butter: palette.butter, sage: palette.sage, ice: palette.ice, blue: palette.blue,
} as const;
export const predictionCalls = {
  damaging: palette.rose, tolerated: palette.sage, uncertain: palette.butter,
};
// Review stars encode evidence review status, independently of variant consequences.
export const reviewColors = { filled: '#b88210', empty: '#7b8490' } as const;
export const consequenceColors: Record<string, string> = {
  missense: palette.apricot, 'stop-gained': palette.rose, 'start-lost': palette.coral,
  'stop-lost': palette.peach, synonymous: palette.sage, splice: palette.blue,
  frameshift: palette.butter, inframe: palette.cyan, other: palette.ice,
};
export const frequencyColors = { low: predictionTextColor(palette.blue), high: '#1d3557' };

// Categorical, not ranked. The exact source code remains the primary identifier.
export const evidenceCodeColors: Record<string, string> = {
  EXP: palette.sage, IDA: palette.blue, IPI: palette.rose, IMP: palette.apricot,
  IGI: palette.cyan, IEP: palette.butter, HTP: palette.leaf, HDA: palette.coral,
  HMP: palette.peach, HGI: palette.ice, HEP: palette.mist,
  IBA: palette.blue, IBD: palette.cyan, IKR: palette.sage, IRD: palette.rose,
  ISS: palette.ice, ISO: palette.blue, ISA: palette.cyan, ISM: palette.apricot,
  IGC: palette.leaf, RCA: palette.sage, TAS: palette.butter, NAS: palette.peach,
  IC: palette.mist, ND: palette.missing, IEA: palette.blue,
};

// Fixed 0–1 display scale for conservation and interface scores. Stops are colour
// anchors only: no threshold, rank transform, or per-protein normalisation.
export type SequenceScoreScale = 'jsd' | 'interface';
// Restore the exact RGB mapping in GitHub main (2dffcfb), shared by sequence and structure.
export const sequenceScoreStops = {
  jsd: ['#F5F0FF', '#8055C0'],
  interface: ['#E0F2FE', '#2563EB', '#6D28D9'],
} as const;
export const sequenceScoreGradient = (scale: SequenceScoreScale) => `linear-gradient(90deg, ${sequenceScoreStops[scale].join(', ')})`;
export const bindingSiteColor = '#DB2777';
export function sequenceScoreColor(value: number, scale: SequenceScoreScale): string {
  const stops = sequenceScoreStops[scale];
  const position = Math.max(0, Math.min(1, value)) * (stops.length - 1);
  const i = Math.min(Math.floor(position), stops.length - 2);
  return interpolateColor(stops[i], stops[i + 1], position - i);
}

/** Keep hue and saturation; lower brightness only as far as readable text requires. */
export function predictionTextColor(fill: string): string {
  const channels = [1, 3, 5].map(i => parseInt(fill.slice(i, i + 2), 16));
  for (let factor = 1; factor >= 0; factor -= .01) {
    const rgb = channels.map(c => Math.round(c * factor));
    const linear = rgb.map(c => c / 255).map(c => c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4);
    const luminance = linear[0] * .2126 + linear[1] * .7152 + linear[2] * .0722;
    // 5.0 leaves room for subtle hover and alternating table backgrounds.
    if (1.05 / (luminance + .05) >= 5) return '#' + rgb.map(c => c.toString(16).padStart(2, '0')).join('');
  }
  return '#000000';
}

export function predictionRamp(value: number, directional = true): string {
  const stops = directional
    ? [palette.sage, palette.butter, palette.apricot, palette.coral, palette.rose]
    : [palette.ice, palette.blue, frequencyColors.high];
  const position = Math.max(0, Math.min(1, value)) * (stops.length - 1);
  const i = Math.min(Math.floor(position), stops.length - 2);
  return interpolateColor(stops[i], stops[i + 1], position - i);
}

export function interpolateColor(low: string, high: string, value: number): string {
  const t = Math.max(0, Math.min(1, value));
  return '#' + [1, 3, 5].map(i => {
    const a = parseInt(low.slice(i, i + 2), 16), b = parseInt(high.slice(i, i + 2), 16);
    return Math.round(a + (b - a) * t).toString(16).padStart(2, '0');
  }).join('');
}

export function textOnColor(hex: string): string {
  const channels = [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map(c => c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4);
  const luminance = channels[0] * .2126 + channels[1] * .7152 + channels[2] * .0722;
  // Black/white keep the full continuous ramp readable, including its middle tones.
  return luminance > .179 ? '#000000' : '#ffffff';
}

/** Shared by CSS legends/boundaries and canvas/SVG marks. */
export const scientificCssVariables = {
  '--sequence-domain': palette.apricot, '--sequence-membrane': palette.blue,
  '--sequence-ptm': palette.rose, '--sequence-jsd-gradient': sequenceScoreGradient('jsd'),
  '--sequence-score-gradient': sequenceScoreGradient('interface'),
  '--clinical-pathogenic': clinicalColors.pathogenic, '--clinical-benign': clinicalColors.benign,
  '--clinical-uncertain': clinicalColors.uncertain, '--clinical-conflicting': clinicalColors.conflicting,
  '--evidence-damaging': evidenceInk.damaging, '--evidence-tolerated': evidenceInk.tolerated,
  '--evidence-uncertain': evidenceInk.uncertain,
  '--review-star-filled': reviewColors.filled, '--review-star-empty': reviewColors.empty,
  '--scientific-link': predictionTextColor('#457b9d'), '--scientific-ink': '#1d3557',
  '--frequency-low': frequencyColors.low, '--frequency-high': frequencyColors.high,
  ...Object.fromEntries(Object.entries(consequenceColors).map(([key, fill]) => [`--consequence-${key}`, predictionTextColor(fill)])),
  ...Object.fromEntries(Object.entries(clinicalColors).map(([key, fill]) => [`--clinical-${key}-ink`, predictionTextColor(fill)])),
};
