import { useEffect, useId, useMemo, useRef, useState } from 'react';
import { ArrowRight } from 'lucide-react';
import { AnimatePresence, motion } from 'motion/react';
import { useReducedMotion } from '@/lib/use-reduced-motion';
import { featureStyle, sourceColors, type Feature, type Track } from './sequence-model';
import { Modal, PageJump } from './ui';
import './compact-sequence-tracks.css';

export interface CompactAnnotationTrackProps {
  track: Track;
  /** One-based, inclusive bounds; the SVG plotting extent is exactly 0..1000. */
  range: [number, number];
  onFeature: (feature: Feature) => void;
  source?: string | string[];
  colourBy?: 'type' | 'source';
  /** Only affects domain tracks. Region/processing annotations get separate lanes. */
  showRegions?: boolean;
  /** Advanced processing/context features, including Chain and Signal; default off. */
  showProcessing?: boolean;
  selectedPosition?: number | null;
}
type Item = { feature: Feature; x: number; width: number; center: number; point: boolean; lane: number };
type Mark = { items: Item[]; left: number; right: number; center: number; lane: number; bin?: [number, number] };
const positionLabel = (feature: Feature) => feature.start === feature.end ? String(feature.start) : `${feature.start}–${feature.end}`;
const originalLabel = (feature: Feature) => feature.label || feature.source_type || feature.type || 'Source annotation';
const sourceLabel = (feature: Feature) => feature.source || 'Source unavailable';
const isDomain = (feature: Feature) => feature.source === 'Pfam' || /^domain$/i.test(feature.source_type ?? feature.type ?? '');
const isDomainRegion = (feature: Feature) => isDomain(feature) || /^(?:repeat|region|motif|coiled coil)$/i.test(feature.source_type ?? feature.type ?? '');
const featureDescription = (feature: Feature) => `${originalLabel(feature)} · ${positionLabel(feature)} · ${sourceLabel(feature)}`;
function recordSummary(features: Feature[]) {
  const ids = new Set<string>();
  let unknown = 0;
  for (const feature of features) {
    if (Array.isArray(feature.record_ids)) feature.record_ids.forEach(id => ids.add(`${feature.source ?? ''}:${id}`));
    else unknown++;
  }
  if (unknown === features.length) return `${features.length} ${features.length === 1 ? 'annotation' : 'annotations'}`;
  return `${features.length} ${features.length === 1 ? 'annotation' : 'annotations'} · ${ids.size} linked source records${unknown ? ' + uncounted records' : ''}`;
}
function FeatureChoices({features,track,onFeature}:{features:Feature[];track:Track;onFeature:(feature:Feature)=>void}) {
  const [page,setPage] = useState(0);
  const limit = 20;
  useEffect(() => {setPage(0);},[features]);
  return <><p className="compact-cluster-summary">{recordSummary(features)} · original positions and sources</p><div className="compact-cluster-list">{features.slice(page * limit, (page + 1) * limit).map((feature,index) => <button key={`${feature.id ?? ''}:${page}:${index}`} onClick={() => onFeature(feature)}><i style={{background:featureStyle(feature,track.id).color}}/><strong>{positionLabel(feature)}</strong><span>{originalLabel(feature)}<small>{sourceLabel(feature)}{Array.isArray(feature.record_ids) ? ` · ${feature.record_ids.length} linked source records` : ''}</small></span><ArrowRight size={15}/></button>)}</div>{features.length > limit && <div className="compact-cluster-pager"><span>{page * limit + 1}–{Math.min(features.length,(page + 1) * limit)} of {features.length} annotations</span><button className="button" disabled={!page} onClick={() => setPage(page - 1)}>Previous</button><PageJump page={page} onJump={setPage} totalPages={Math.max(1,Math.ceil(features.length/limit))} label="Cluster annotation page"/><button className="button" disabled={(page + 1) * limit >= features.length} onClick={() => setPage(page + 1)}>Next</button></div>}</>;
}

export function CompactAnnotationTrack({track,range,onFeature,source='all',colourBy='type',showRegions=false,showProcessing=false,selectedPosition}:CompactAnnotationTrackProps) {
  const host = useRef<HTMLDivElement>(null);
  const [width,setWidth] = useState(1000);
  const [hover,setHover] = useState<Mark|null>(null);
  const [cluster,setCluster] = useState<Feature[]|null>(null);
  const tooltipId = useId();
  const reduceMotion = useReducedMotion();
  const span = Math.max(1,range[1] - range[0] + 1);
  useEffect(() => {
    if (!host.current) return;
    const observer = new ResizeObserver(entries => setWidth(Math.max(1,entries[0].contentRect.width)));
    observer.observe(host.current);
    return () => observer.disconnect();
  },[]);
  useEffect(() => {setHover(null);setCluster(null);},[track,range[0],range[1],source,showRegions,showProcessing]);
  const selectedSources=Array.isArray(source)?source:null;
  const features = useMemo(() => track.features.filter(feature =>
    Number.isFinite(feature.start) && Number.isFinite(feature.end) && feature.start >= 1 && feature.end >= feature.start &&
    feature.end >= range[0] && feature.start <= range[1] &&
    (source === 'all' || (selectedSources ? selectedSources.includes(sourceLabel(feature)) : sourceLabel(feature) === source)) &&
    (track.id !== 'domains' || isDomain(feature) || (showRegions && isDomainRegion(feature)) || (showProcessing && !isDomainRegion(feature)))
  ),[track,range[0],range[1],source,selectedSources,showRegions,showProcessing]);
  const tone = (feature:Feature) => {
    if (colourBy === 'source') return {name:sourceLabel(feature),color:sourceColors[feature.source ?? ''] ?? '#64748b'};
    const style = featureStyle(feature,track.id);
    // Only source-annotated turns are drawn; gaps are not inferred loops.
    return track.id === 'secondary' && style.name === 'Turn / loop'
      ? {...style,name:feature.source_type || feature.type || feature.label || 'Source secondary annotation'}
      : style;
  };
  const laneKey = (feature:Feature) => track.id === 'domains'
    ? `${isDomain(feature) ? 'Domain' : isDomainRegion(feature) ? 'Region' : 'Processing / context'} · ${sourceLabel(feature)}`
    : track.id === 'membrane' ? String(feature.topology_label??sourceLabel(feature))
    : track.id === 'ptm' ? sourceLabel(feature) : 'Annotations';
  const laneKeys = ['domains','membrane','ptm'].includes(track.id)
    ? [...new Set(features.map(laneKey))].sort((a,b) => {if(track.id!=='domains')return a.localeCompare(b);const rank=(key:string)=>key.startsWith('Domain')?0:key.startsWith('Region')?1:2;return rank(a)-rank(b)||a.localeCompare(b);})
    : ['Annotations'];
  const laneCount = Math.max(1,laneKeys.length);
  const plotHeight = ['domains','membrane'].includes(track.id) ? Math.max(38,laneCount * 18 + 4)
    : track.id === 'secondary' ? 42 : track.id === 'ptm' ? Math.max(56,laneCount * 30 + 4) : 32;
  const laneHeight = (plotHeight - 4) / laneCount;
  const markHeight = track.id === 'secondary' ? 22 : track.id === 'domains' ? 14 : 12;
  const unitPerPixel = 1000 / width;
  const items:Item[] = features.map(feature => {
    const left = (Math.max(feature.start,range[0]) - range[0]) / span * 1000;
    const extent = (Math.min(feature.end,range[1]) - Math.max(feature.start,range[0]) + 1) / span * 1000;
    return {feature,x:left,width:extent,center:left + extent / 2,point:feature.start === feature.end,lane:Math.max(0,laneKeys.indexOf(laneKey(feature)))};
  });
  const marks:Mark[] = [];
  if (track.id === 'ptm') {
    // Bins are only a display aid. All features, source record IDs and positions survive selection.
    const binWidth = Math.max(1,Math.ceil(span / Math.max(1,Math.floor(width / 24))));
    const bins = new Map<string,Item[]>();
    for (const item of items) {
      const position = Math.max(range[0],item.feature.start);
      const key = Math.floor((position - range[0]) / binWidth);
      const laneKey = `${item.lane}:${key}`;
      const bin = bins.get(laneKey) ?? [];
      bin.push(item);bins.set(laneKey,bin);
    }
    for (const [compoundKey,binItems] of bins) {
      const key = Number(compoundKey.split(':')[1]);
      const low = range[0] + key * binWidth;
      const high = Math.min(range[1],low + binWidth - 1);
      const center = binItems.length === 1 ? binItems[0].center : ((low + high) / 2 - range[0] + .5) / span * 1000;
      marks.push({items:binItems,left:Math.max(0,center - 10 * unitPerPixel),right:Math.min(1000,center + 10 * unitPerPixel),center,lane:binItems[0].lane,bin:[low,high]});
    }
    // Boundary-near single sites can still collide across bins. Keep them selectable
    // in one aggregate rather than letting a larger marker cover another site.
    marks.sort((a,b) => a.center - b.center);
    for (let index = 1; index < marks.length;) {
      const previous = marks[index - 1], current = marks[index];
      if (current.lane === previous.lane && current.left < previous.right) {
        previous.items.push(...current.items);
        previous.bin = [Math.min(previous.bin![0],current.bin![0]),Math.max(previous.bin![1],current.bin![1])];
        previous.center = ((previous.bin[0] + previous.bin[1]) / 2 - range[0] + .5) / span * 1000;
        previous.left = Math.max(0,previous.center - 10 * unitPerPixel);
        previous.right = Math.min(1000,previous.center + 10 * unitPerPixel);
        marks.splice(index,1);
      } else index++;
    }
  } else {
    // Overlapping hit targets share a selector, not a biological merged annotation.
    for (let lane = 0; lane < laneCount; lane++) {
      const ordered = items.filter(item => item.lane === lane).sort((a,b) => a.x - b.x || a.width - b.width);
      let previous:Mark|undefined;
      for (const item of ordered) {
        const left = Math.max(0,Math.min(item.x,item.center - 4 * unitPerPixel));
        const right = Math.min(1000,Math.max(item.x + item.width,item.center + 4 * unitPerPixel));
        if (previous && left <= previous.right) {
          previous.items.push(item);previous.right = Math.max(previous.right,right);previous.center = (previous.left + previous.right) / 2;
        } else {
          previous = {items:[item],left,right,center:(left + right) / 2,lane};marks.push(previous);
        }
      }
    }
  }
  const legend = [...new Map(features.map(feature => {
    const style = tone(feature);
    const name = track.id === 'domains' ? `${sourceLabel(feature)}${isDomain(feature) ? '' : isDomainRegion(feature) ? ' regions' : ' processing'}` : style.name;
    return [name,{...style,name}];
  })).values()];
  const open = (mark:Mark) => {
    const originals = mark.items.map(item => item.feature);
    if (originals.length === 1) onFeature(originals[0]);
    else setCluster(originals);
    setHover(null);
  };
  const hoverFeatures = hover?.items.map(item => item.feature) ?? [];
  return <div className={`compact-annotation-track compact-${track.id}`} ref={host}>
    <svg viewBox={`0 0 1000 ${plotHeight}`} preserveAspectRatio="none" style={{height:plotHeight}} aria-label={`${track.label}: ${features.length} annotations, residues ${range[0]}–${range[1]}`}>
      {laneKeys.map((key,index) => <line key={key} x1="0" x2="1000" y1={2 + laneHeight * (index + .5) + (track.id === 'ptm' ? 5 : 0)} y2={2 + laneHeight * (index + .5) + (track.id === 'ptm' ? 5 : 0)} stroke="#e6edf5" strokeWidth="1" vectorEffect="non-scaling-stroke"/>)}
      {marks.map((mark,index) => {
        const originals = mark.items.map(item => item.feature);
        const label = originals.length === 1 ? featureDescription(originals[0]) : `${recordSummary(originals)}${mark.bin ? ` · display bin ${mark.bin[0]}–${mark.bin[1]}` : ''} · ${[...new Set(originals.map(sourceLabel))].join(', ')}`;
        const y = 2 + laneHeight * (mark.lane + .5) + (track.id === 'ptm' ? 5 : 0);
        const colors = [...new Set(originals.map(feature => tone(feature).color))];
        return <g key={`${mark.lane}:${index}`} className="compact-feature-mark" role="button" tabIndex={0} aria-label={`${label}. Open source annotation${originals.length > 1 ? ' selector' : ''}`} aria-describedby={hover?.items[0].feature === mark.items[0].feature ? tooltipId : undefined} onMouseEnter={() => setHover(mark)} onMouseLeave={event => {if(document.activeElement !== event.currentTarget)setHover(null);}} onFocus={() => setHover(mark)} onBlur={() => setHover(null)} onClick={() => open(mark)} onKeyDown={event => {if(event.key === 'Enter' || event.key === ' '){event.preventDefault();open(mark);}else if(event.key==='Escape'){setHover(null);}}}>
          <title>{label}</title>
          {track.id === 'ptm' ? <>
            {colors.map((color,colorIndex) => <rect key={color} x={mark.center - (originals.length > 1 ? 7 : 5) * unitPerPixel} y={y - 11 + colorIndex * 22 / colors.length} width={(originals.length > 1 ? 14 : 10) * unitPerPixel} height={22 / colors.length} fill={color} rx={colors.length === 1 ? 3 : 0}/>)}
            {originals.length > 1 && <text className="compact-ptm-count" transform={`translate(${mark.center} ${y - 16}) scale(${unitPerPixel} 1)`} textAnchor="middle" pointerEvents="none">{originals.length}</text>}
          </> : mark.items.map((item,itemIndex) => {
            const color = tone(item.feature).color;
            return item.point ? <line key={itemIndex} x1={item.center} x2={item.center} y1={y - markHeight / 2} y2={y + markHeight / 2} stroke={color} strokeWidth="4" vectorEffect="non-scaling-stroke"/> : <rect key={itemIndex} x={item.x} y={y - markHeight / 2} width={item.width} height={markHeight} rx="2" fill={color} stroke="white" strokeWidth=".5" vectorEffect="non-scaling-stroke"/>;
          })}
          <rect className="compact-hit-area" x={mark.left} y={2 + laneHeight * mark.lane} width={Math.max(unitPerPixel,mark.right - mark.left)} height={laneHeight} fill="transparent"/>
        </g>;
      })}
      {selectedPosition != null && selectedPosition >= range[0] && selectedPosition <= range[1] && <line className="compact-selected-position" x1={(selectedPosition - range[0] + .5) / span * 1000} x2={(selectedPosition - range[0] + .5) / span * 1000} y1="0" y2={plotHeight} stroke="#183b64" strokeWidth="1.2" strokeDasharray="3 2" vectorEffect="non-scaling-stroke" pointerEvents="none"/>}
    </svg>
    {laneKeys.length>1&&<div className="compact-track-lanes" aria-label="Independent annotation lanes"><em>Top to bottom</em>{laneKeys.map((key,index)=><span key={key}><b>{index+1}</b>{key}</span>)}</div>}
    <div className="compact-track-legend">{features.length ? legend.map(item => <span key={item.name}><i style={{background:item.color}}/>{item.name}</span>) : <span>No {source !== 'all' ? `${Array.isArray(source)?source.join(' + '):source} ` : ''}annotations in this range</span>}{track.id === 'ptm' && marks.some(mark=>mark.items.length>1) && <span className="compact-aggregate-key">Numbers = position/type annotations</span>}</div>
    <AnimatePresence>{hover && <motion.div className="compact-track-tooltip" id={tooltipId} role="tooltip" initial={{opacity:reduceMotion?1:0,y:reduceMotion?0:3}} animate={{opacity:1,y:0}} exit={{opacity:0,y:reduceMotion?0:2}} transition={{duration:reduceMotion?0:.12}}><strong>{recordSummary(hoverFeatures)}</strong>{hover.bin && hoverFeatures.length > 1 && <small>Display bin {hover.bin[0]}–{hover.bin[1]}</small>}{hoverFeatures.slice(0,4).map((feature,index) => <span key={index}>{featureDescription(feature)}</span>)}{hoverFeatures.length > 4 && <small>+{hoverFeatures.length - 4} original annotations · click to choose</small>}</motion.div>}</AnimatePresence>
    {cluster && <Modal title={`${track.label} · original annotations`} onClose={() => setCluster(null)}><FeatureChoices features={cluster} track={track} onFeature={feature => {setCluster(null);onFeature(feature);}}/></Modal>}
  </div>;
}
export default CompactAnnotationTrack;
