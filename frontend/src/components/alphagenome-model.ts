import type { CSSProperties } from 'react';
import { palette } from '../lib/palette';

/** Source API contracts and modality metadata shared by the workspace and tracks. */
export type Track = {
  track_id: string;
  modality: string;
  name: string;
  assay_title: string;
  biosample_name: string | null;
  biosample_type: string | null;
  biosample_key?: string;
  ontology_curie: string | null;
  gtex_tissue?: string | null;
  strand: string | null;
  histone_mark: string | null;
  transcription_factor?: string | null;
  data_source: string | null;
  display_unit: string;
};
export type Tile = {
  tile_id: string;
  window_start_0based: number;
  window_end_0based: number;
  chromosome: string;
};
export type Gene = {
  ensembl_gene_id: string;
  gene_symbol: string;
  gene_start_1based: number;
  gene_end_1based_inclusive: number;
  gene_strand: string;
  status?: string;
  prediction_status?: string;
  tiles: Tile[];
};
export type Catalog = {
  available: boolean;
  genes: Gene[];
  tracks: Track[];
  snapshot: string;
  levels: number[];
  missing_modalities: string[];
  shared_modalities?: string[];
};
export type TranscriptFeature = {
  feature: 'CDS' | 'stop_codon' | 'exon' | 'UTR';
  start_0based: number;
  end_0based: number;
  exon_number: number;
  strand: string;
};
export type ManeModel = {
  status: string;
  transcript_id: string | null;
  segments: TranscriptFeature[];
  exons?: TranscriptFeature[];
  utrs?: TranscriptFeature[];
  transcript_start_0based?: number | null;
  transcript_end_0based?: number | null;
  cds_bases: number;
  cds_segments: number;
  chromosome: string;
  strand: string;
};
export type Region = { start: number; end: number; chromosome: string };
export type Signal = Region & {
  kind: 'signal';
  mean: (number | null)[];
  maximum: (number | null)[];
  bin_width: number;
  bin_edges?: number[];
  source_resolution_bp?: number;
};
export type Contacts = Region & {
  kind: 'contacts';
  size: number;
  values: (number | null)[];
  bin_width: number;
  bin_edges?: number[];
  source_resolution_bp?: number;
};
export type Junction = {
  rank: number;
  source_event_index?: number;
  start_0based: number;
  end_0based: number;
  strand: string;
  value: number | null;
};
export type Junctions = Region & {
  kind: 'junctions';
  items: Junction[];
  total: number;
  has_more: boolean;
  offset: number;
};
export type TrackData = Signal | Contacts | Junctions;
export const modes: Record<
  string,
  { label: string; color: string; group: string; help: string }
> = {
  rna_seq: {
    label: 'RNA-seq',
    color: palette.blue,
    group: 'Transcription / RNA',
    help: 'Reference-sequence RNA abundance prediction.',
  },
  cage: {
    label: 'CAGE',
    color: palette.cyan,
    group: 'Transcription / RNA',
    help: 'Transcription start-site activity.',
  },
  procap: {
    label: 'PRO-cap',
    color: palette.ice,
    group: 'Transcription / RNA',
    help: 'Nascent transcription initiation.',
  },
  atac: {
    label: 'ATAC',
    color: palette.sage,
    group: 'Accessibility',
    help: 'Chromatin accessibility.',
  },
  dnase: {
    label: 'DNase',
    color: palette.leaf,
    group: 'Accessibility',
    help: 'DNase-sensitive chromatin accessibility.',
  },
  chip_histone: {
    label: 'Histone ChIP',
    color: palette.coral,
    group: 'ChIP',
    help: 'Histone-mark signal.',
  },
  chip_tf: {
    label: 'TF ChIP',
    color: palette.rose,
    group: 'ChIP',
    help: 'Transcription-factor binding signal.',
  },
  splice_sites: {
    label: 'Splice sites',
    color: palette.peach,
    group: 'Splicing',
    help: 'Shared donor and acceptor site probabilities; not biosample-specific.',
  },
  splice_site_usage: {
    label: 'Splice usage',
    color: palette.apricot,
    group: 'Splicing',
    help: 'Reference-sequence splice-site usage prediction.',
  },
  splice_junctions: {
    label: 'Splice junctions',
    color: palette.butter,
    group: 'Splicing',
    help: 'Predicted spliced-read connections.',
  },
  contact_maps: {
    label: 'Contact map',
    color: palette.mist,
    group: '3D genome',
    help: 'Signed contact enrichment relative to genomic-distance expectation.',
  },
};

export const contextName = (t: Track) =>
  t.biosample_name || 'Shared prediction';
export const sceneKey = (t: Track) => t.biosample_key || t.ontology_curie || '';
export const details = (t: Track) =>
  [
    t.assay_title,
    t.histone_mark,
    t.transcription_factor,
    t.strand && t.strand !== '.' ? `${t.strand} strand` : null,
  ]
    .filter(Boolean)
    .join(' · ');
export const colorStyle = (color: string) =>
  ({ '--ag-color': color }) as CSSProperties;
export const modeInfo = (id: string) =>
  modes[id] ?? { label: id, color: '#55606c', group: 'Prediction', help: '' };
export const signalModality = (t: Track) =>
  !['contact_maps', 'splice_junctions'].includes(t.modality);
