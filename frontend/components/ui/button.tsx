import { ButtonHTMLAttributes } from "react";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "quiet" };

export function Button({ variant = "secondary", className = "", type = "button", ...props }: Props) {
  return <button type={type} className={`ui-button ui-button-${variant} ${className}`.trim()} {...props} />;
}
