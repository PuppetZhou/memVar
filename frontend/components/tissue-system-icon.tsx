import { type CSSProperties } from "react";
import { TISSUE_SYSTEMS, type TissueSystemId, tissueIconAssetForKey, tissueVisualForRegion } from "../lib/tissue-visuals";

type TissueSystemIconProps = {
  systemId?: TissueSystemId;
  bodyRegionId?: string;
  className?: string;
  size?: number;
  /** The selected state uses the locally shipped official Healthicons filled file. */
  selected?: boolean;
};

/**
 * A deliberately small, locally bundled Healthicons family. Outline is the
 * default; selected uses the matched filled upstream asset. These icons are
 * decorative because every use retains the visible text label.
 */
export function TissueSystemIcon({ systemId, bodyRegionId, className, size = 18, selected = false }: TissueSystemIconProps) {
  const iconKey = bodyRegionId ? tissueVisualForRegion(bodyRegionId).iconKey : systemId ? tissueVisualForSystem(systemId).iconKey : null;
  if (!iconKey) throw new Error("TissueSystemIcon requires a bodyRegionId or systemId");
  const asset = tissueIconAssetForKey(iconKey);
  if (!asset) return null;
  const iconPath = selected ? asset.filledPath : asset.outlinePath;
  const style: CSSProperties = {
    width: size,
    height: size,
    display: "inline-block",
    flex: "0 0 auto",
    backgroundColor: "currentColor",
    mask: `url(${iconPath}) center / contain no-repeat`,
    WebkitMask: `url(${iconPath}) center / contain no-repeat`,
  };
  return <span className={className} data-healthicon={asset.originalName} data-selected={selected || undefined} aria-hidden="true" style={style} />;
}

function tissueVisualForSystem(systemId: TissueSystemId) {
  const visual = TISSUE_SYSTEMS.find((system) => system.id === systemId);
  if (!visual) throw new Error(`Missing tissue system visual: ${systemId}`);
  return visual;
}
