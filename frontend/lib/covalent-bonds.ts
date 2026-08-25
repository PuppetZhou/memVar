/**
 * Present the source-supplied covalent feature type without inferring a bond
 * class that is absent from UniProt. The S—S notation is an explanatory
 * synonym only for an explicitly supplied disulfide-bond record.
 */
export function covalentBondLabel(featureType: string | null | undefined): string {
  const sourceType = featureType?.trim();
  if (!sourceType) return "Covalent bond (type not specified)";
  if (sourceType.toLocaleLowerCase() === "disulfide bond") return "Disulfide bond (S—S)";
  return sourceType;
}

export type CovalentPairLike = {
  start_endpoint: number;
  end_endpoint: number;
  feature_type?: string | null;
};

export function isDisulfideBond(featureType: string | null | undefined): boolean {
  return featureType?.trim().toLocaleLowerCase() === "disulfide bond";
}

export function allCovalentPairsAreDisulfide(pairs: readonly CovalentPairLike[]): boolean {
  return pairs.length > 0 && pairs.every((pair) => isDisulfideBond(pair.feature_type));
}

/**
 * Greedy interval routing for the sequence arc diagram. Intervals that do not
 * overlap reuse a lane; overlapping/nested pairs climb into separate lanes up
 * to the visual cap. The result follows input order so biological records are
 * never reordered or merged.
 */
export function routeCovalentPairLanes(
  pairs: readonly Pick<CovalentPairLike, "start_endpoint" | "end_endpoint">[],
  maxLanes = 8,
): number[] {
  if (!Number.isInteger(maxLanes) || maxLanes < 1) throw new Error("maxLanes must be a positive integer");
  const laneByInput = Array<number>(pairs.length).fill(0);
  const laneEnds: number[] = [];
  const ordered = pairs.map((pair, inputIndex) => ({
    inputIndex,
    start: Math.min(pair.start_endpoint, pair.end_endpoint),
    end: Math.max(pair.start_endpoint, pair.end_endpoint),
  })).sort((left, right) => left.start - right.start || left.end - right.end || left.inputIndex - right.inputIndex);

  for (const interval of ordered) {
    let lane = laneEnds.findIndex((end) => end < interval.start);
    if (lane < 0 && laneEnds.length < maxLanes) {
      lane = laneEnds.length;
      laneEnds.push(interval.end);
    } else if (lane < 0) {
      lane = laneEnds.reduce((best, end, index) => end < laneEnds[best] ? index : best, 0);
      laneEnds[lane] = Math.max(laneEnds[lane], interval.end);
    } else {
      laneEnds[lane] = interval.end;
    }
    laneByInput[interval.inputIndex] = lane;
  }
  return laneByInput;
}
