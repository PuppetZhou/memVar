import { ReactionEquation } from './ReactionEquation';
import type { CSSProperties } from 'react';
import { ArrowRight, BookOpen, FlaskConical, SlidersHorizontal, Zap } from 'lucide-react';
import { display, label, type RecordData } from '../api';
import { Disclosure, Fields, LinkOut } from './ui';
import { Button } from './ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { ContentTransition } from '../lib/motion';
import './functional-context.css';

const categories = [
  { type: 'CATALYTIC ACTIVITY', title: 'Catalytic activity', icon: Zap, color: 'var(--teal-11)' },
  { type: 'COFACTOR', title: 'Cofactors', icon: FlaskConical, color: 'var(--amber-11)' },
  { type: 'ACTIVITY REGULATION', title: 'Activity regulation', icon: SlidersHorizontal, color: 'var(--indigo-11)' },
  { type: 'SIMILARITY', title: 'Protein family', icon: BookOpen, color: 'var(--violet-11)' },
];

const tabValue = (type: string) => type.toLowerCase().replaceAll(' ', '-');

function text(value: unknown): string {
  if (Array.isArray(value)) return value.map(text).filter(Boolean).join('\n\n');
  if (value && typeof value === 'object') {
    const item = value as RecordData;
    return text(item.text ?? item.texts ?? item.value ?? item.name ?? '');
  }
  return value == null ? '' : String(value);
}
function scope(item: RecordData) {
  return item.scope_label ? display(item.scope_label) : item.scope_type === 'entry' ? 'Protein entry' : label(item.scope_type);
}
function annotationParts(item: RecordData) {
  const details = (item.details ?? {}) as RecordData;
  const reaction = (details.reaction ?? {}) as RecordData;
  const cofactors = Array.isArray(details.cofactors) ? details.cofactors as RecordData[] : [];
  const evidence = [
    ...(Array.isArray(details.texts) ? details.texts.flatMap(item => Array.isArray(item.evidences) ? item.evidences : []) : []),
    ...(Array.isArray(reaction.evidences) ? reaction.evidences : []),
    ...cofactors.flatMap(item => Array.isArray(item.evidences) ? item.evidences : []),
  ] as RecordData[];
  return { reaction, cofactors, evidence, narrative: text(item.text ?? reaction.name) || cofactors.map(item => text(item.name)).filter(Boolean).join(' · ') };
}
function EvidenceLinks({ items }: { items: RecordData[] }) {
  return <div className="fc-references">{items.map((item, index) => <span key={index}>
    {item.source === 'PubMed' && item.id ? <LinkOut href={`https://pubmed.ncbi.nlm.nih.gov/${item.id}/`}>PMID:{display(item.id)}</LinkOut>
      : [item.source, item.id].filter(Boolean).map(display).join(' · ')}
    {Boolean(item.evidenceCode) && <small>{display(item.evidenceCode)}</small>}
  </span>)}</div>;
}
function Annotation({ item, index }: { item: RecordData; index: number }) {
  const { reaction, cofactors, evidence, narrative } = annotationParts(item);
  return <article className="fc-annotation">
    <div className="fc-annotation-meta"><span>Annotation {index + 1} · {scope(item)}</span>{Boolean(item.mapping_status) && <span>{label(item.mapping_status)}</span>}</div>
    {narrative && (item.comment_type==='CATALYTIC ACTIVITY'?<ReactionEquation text={narrative}/>:<p className="fc-full-text">{narrative}</p>)}
    {Boolean(reaction.ecNumber) && <p className="fc-ec">EC {display(reaction.ecNumber)}</p>}
    {cofactors.map((item, index) => <Fields key={index} items={[{ label: 'Cofactor', value: item.name }, { label: 'ChEBI', value: (item.cofactorCrossReference as RecordData | undefined)?.id }]} />)}
    {evidence.length > 0 && <Disclosure title={`Source references · ${evidence.length}`}><EvidenceLinks items={evidence} /></Disclosure>}
    {Boolean(item.annotation_id) && <small className="fc-record-id">{display(item.annotation_id)}</small>}
  </article>;
}

interface FunctionalContextProps {
  annotations: RecordData[];
  accession: string;
  activeType: string;
  onTypeChange: (type: string) => void;
  onDetails?: () => void;
  full?: boolean;
}

/** The preview takes the first existing source record, without deriving a representative annotation. */
function FunctionalContext({ annotations, accession, activeType, onTypeChange, onDetails, full = false }: FunctionalContextProps) {
  const available = categories.map(category => ({ ...category, rows: annotations.filter(item => item.comment_type === category.type) })).filter(category => category.rows.length);
  const selected = available.find(category => category.type === activeType) ?? available[0];
  const sourceLink = <LinkOut href={`https://www.uniprot.org/uniprotkb/${accession}/entry#function`}>Function at UniProt</LinkOut>;
  if (!selected) return <div className="fc-empty"><p>No structured functional context is available.</p>{sourceLink}</div>;
  return <div className={`functional-context${full ? ' fc-detail' : ' fc-summary'}`}>
    <Tabs orientation="vertical" value={tabValue(selected.type)} onValueChange={value => { const category = available.find(item => tabValue(item.type) === value); if (category) onTypeChange(category.type); }} className="fc-tabs">
      <TabsList aria-label="Functional annotation categories" variant="line" className="fc-category-list">
        {available.map(category => <TabsTrigger key={category.type} value={tabValue(category.type)} className="fc-category" style={{ '--fc-color': category.color } as CSSProperties}>
          <category.icon aria-hidden="true" /><span>{category.title}<small>{category.rows.length} source {category.rows.length === 1 ? 'annotation' : 'annotations'}</small></span>
        </TabsTrigger>)}
      </TabsList>
      <ContentTransition transitionKey={selected.type} className="fc-content">
        {available.map(category => {
          const first = category.rows[0], { reaction, narrative } = annotationParts(first);
          return <TabsContent key={category.type} value={tabValue(category.type)} forceMount={full || undefined} hidden={category.type !== selected.type} inert={category.type !== selected.type} className="fc-panel" style={{ '--fc-color': category.color } as CSSProperties}>
            <div className="fc-panel-heading"><category.icon size={17} aria-hidden="true"/><h4>{category.title}</h4></div>
            {full ? category.rows.map((item, index) => <Annotation key={String(item.annotation_id ?? index)} item={item} index={index} />) : <>
              <div className="fc-preview-meta">UniProt · {scope(first)}<span>Annotation 1 of {category.rows.length}</span></div>
              {Boolean(reaction.ecNumber) && <span className="fc-ec">EC {display(reaction.ecNumber)}</span>}
              {narrative ? (category.type==='CATALYTIC ACTIVITY'?<ReactionEquation text={narrative}/>:<p className="fc-preview-text">{narrative}</p>) : <p className="fc-empty">No narrative text is supplied for this annotation. Source fields remain available.</p>}
            </>}
          </TabsContent>;
        })}
        {!full && <Button variant="link" size="sm" onClick={onDetails} className="fc-open-evidence">Read annotation & evidence <ArrowRight data-icon="inline-end"/></Button>}
      </ContentTransition>
    </Tabs>
    <div className="fc-source">{sourceLink}</div>
  </div>;
}

export function FunctionSummary(props: Omit<FunctionalContextProps, 'full'>) { return <FunctionalContext {...props}/>; }
export function FunctionDetails(props: Omit<FunctionalContextProps, 'full' | 'onDetails'>) { return <FunctionalContext {...props} full/>; }
