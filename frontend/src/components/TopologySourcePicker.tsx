import { useId, useState } from 'react';
import { Popover } from 'radix-ui';
import { ChevronDown, SlidersHorizontal } from 'lucide-react';
import { annotationSourceGuide, type AnnotationSourceOption } from './sequence-model';
import './topology-source-picker.css';

const kinds: Record<string, string> = {
  source_annotation: 'Database annotation', prediction: 'Prediction', method_prediction: 'Prediction',
  integrated_topology: 'Integrated topology', experimental_evidence: 'Experimental evidence', structure_region: 'Structure-derived',
};
export default function TopologySourcePicker({ options, selected, onChange, multiple = false, compact = false }: {
  options: AnnotationSourceOption[]; selected: string[]; onChange: (ids: string[]) => void; multiple?: boolean; compact?: boolean;
}) {
  const id = useId();
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const chosen = options.filter(option => selected.includes(option.id));
  const groups = [...new Set(options.map(option => option.source))].sort((a, b) =>
    (a === 'UniProt' ? -2 : a === 'DeepTMHMM2' ? -1 : 0) - (b === 'UniProt' ? -2 : b === 'DeepTMHMM2' ? -1 : 0));
  const summary = chosen.length === 1 ? chosen[0].method ? `${chosen[0].source} · ${chosen[0].method}` : chosen[0].source : chosen.length ? `${chosen.length} layers` : 'Off';
  const choose = (option: AnnotationSourceOption) => {
    onChange(multiple ? selected.includes(option.id) ? selected.filter(value => value !== option.id) : [...selected, option.id] : [option.id]);
    if (!multiple) setOpen(false);
  };
  return <Popover.Root open={open} onOpenChange={value => { setOpen(value); if (value) setSearch(''); }}>
    <Popover.Trigger asChild><button type="button" className={`topology-source-trigger ${compact ? 'is-compact' : ''}`} aria-label={`Topology by source: ${summary}`}>
      <SlidersHorizontal size={14}/><span><strong>{compact ? 'Sources' : 'Topology by source'}</strong><small title={chosen.map(option => option.label).join('; ')}>{summary}</small></span><ChevronDown size={13}/>
    </button></Popover.Trigger>
    <Popover.Portal><Popover.Content className="topology-source-picker" side={compact ? 'right' : 'bottom'} align="start" sideOffset={8} collisionPadding={16} aria-label="Topology by source">
      <header><strong>Topology by source</strong><span>{multiple ? `${chosen.length} selected` : 'Choose one layer'}</span></header>
      <p>{multiple ? 'Compare mapped source layers on the same sequence axis.' : 'Colour the structure using one mapped source layer.'}</p>
      <input type="search" aria-label="Find topology source or method" placeholder="Find source or method…" value={search} onChange={event => setSearch(event.target.value)}/>
      <div className="topology-source-list">{groups.map(source => {
        const entries = options.filter(option => option.source === source && `${option.label} ${option.method ?? ''} ${kinds[option.kind ?? ''] ?? ''}`.toLowerCase().includes(search.toLowerCase()));
        if (!entries.length) return null;
        const choices = entries.map((option, index) => <label key={option.id} className="topology-source-choice" title={annotationSourceGuide(option.source, option.kind).description}>
          <input type={multiple ? 'checkbox' : 'radio'} name={id} checked={selected.includes(option.id)} disabled={option.available === false || (multiple && selected.length >= 20 && !selected.includes(option.id))} onChange={() => choose(option)}/>
          <span><strong>{option.method || (entries.length === 1 ? source : kinds[option.kind ?? ''] || source)}{entries.filter(other => other.label === option.label).length > 1 ? ` · ${index + 1}` : ''}</strong><small>{option.method || entries.length === 1 ? kinds[option.kind ?? ''] || option.kind : option.label}</small></span>
          {typeof option.count === 'number' && <small>{option.count}</small>}
        </label>);
        return entries.length === 1 ? <div key={source}>{choices}</div> : <details key={source} className="topology-source-family"><summary>{source}<span>{entries.filter(option => selected.includes(option.id)).length} selected · {entries.length} layers</span></summary>{choices}</details>;
      })}</div>
      {multiple && <footer><button className="text-button" onClick={() => onChange(['uniprot'])}>Reset to UniProt</button><button className="button" onClick={() => setOpen(false)}>Done</button></footer>}
    </Popover.Content></Popover.Portal>
  </Popover.Root>;
}
