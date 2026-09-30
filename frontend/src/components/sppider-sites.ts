export type SppiderSite = { position: number; partner_count: number };

// Screen-space grouping only: preserve every exact residue and its partner count.
export function groupSppiderMarkers(sites: readonly SppiderSite[], range: readonly [number, number], width: number) {
  const span = range[1] - range[0] + 1;
  const groups = new Map<number, SppiderSite[]>();
  for (const site of sites) {
    if (site.position < range[0] || site.position > range[1]) continue;
    const bin = Math.floor((site.position - range[0] + .5) / span * width / 12);
    const group = groups.get(bin) ?? [];
    group.push(site);
    groups.set(bin, group);
  }
  return [...groups.values()];
}
