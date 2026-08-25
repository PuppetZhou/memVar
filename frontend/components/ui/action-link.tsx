import Link, { LinkProps } from "next/link";
import { AnchorHTMLAttributes, ReactNode } from "react";
import { ExternalLink } from "lucide-react";

type Props = LinkProps & Omit<AnchorHTMLAttributes<HTMLAnchorElement>, keyof LinkProps | "href"> & {
  children: ReactNode;
  external?: boolean;
};

export function ActionLink({ children, external = false, className = "", target, rel, ...props }: Props) {
  return <Link className={`action-link ${className}`.trim()} target={external ? "_blank" : target} rel={external ? "noreferrer" : rel} {...props}>{children}{external && <ExternalLink className="action-link-icon" aria-hidden="true" size={15} strokeWidth={1.9} />}</Link>;
}
