import assert from 'node:assert/strict';
import test from 'node:test';
import { groupSppiderMarkers } from '../src/components/sppider-sites.ts';

test('dense markers share a screen-space group without merging residues or partner counts', () => {
  const sites = [{ position: 1, partner_count: 2 }, { position: 2, partner_count: 5 }, { position: 90, partner_count: 1 }];
  const grouped = groupSppiderMarkers(sites, [1, 100], 100);
  assert.deepEqual(grouped, [sites.slice(0, 2), sites.slice(2)]);
  assert.deepEqual(grouped.flat(), sites);
});

test('zoom separates adjacent residues and excludes sites outside the visible range', () => {
  const sites = [{ position: 1, partner_count: 2 }, { position: 2, partner_count: 5 }, { position: 90, partner_count: 1 }];
  assert.deepEqual(groupSppiderMarkers(sites, [1, 10], 1000), [[sites[0]], [sites[1]]]);
  assert.deepEqual(groupSppiderMarkers(sites, [3, 20], 1000), []);
});
