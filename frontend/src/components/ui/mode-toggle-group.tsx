import { useId, type ComponentPropsWithoutRef, type ReactNode } from 'react';
import { LayoutGroup, motion } from 'motion/react';
import { useReducedMotion } from '@/lib/use-reduced-motion';
import { ToggleGroup as ToggleGroupPrimitive } from 'radix-ui';
import { cn } from '@/lib/utils';
import { uiTransition } from '@/lib/motion';

export type ModeOption<T extends string> = {
  value: T;
  label: ReactNode;
  title?: string;
  disabled?: boolean;
  ariaLabel?: string;
};

type ModeToggleGroupProps<T extends string> = Omit<ComponentPropsWithoutRef<'div'>, 'children' | 'onChange' | 'defaultValue' | 'dir'> & {
  value: T;
  onValueChange: (value: T) => void;
  options: readonly ModeOption<T>[];
  'aria-label': string;
  dir?: 'ltr' | 'rtl';
};

/** shadcn/Radix single ToggleGroup, adapted to the existing dense view controls. */
export function ModeToggleGroup<T extends string>({ value, onValueChange, options, className, ...props }: ModeToggleGroupProps<T>) {
  const id = useId();
  const reduce = useReducedMotion();
  return <LayoutGroup id={id}>
    <ToggleGroupPrimitive.Root {...props} type="single" role="radiogroup" value={`mode:${value}`}
      data-slot="toggle-group" className={cn('mode-toggle-group', className)}
      onValueChange={next => {
        // A display mode must always remain selected; clicking it again is a no-op.
        const option = options.find(option => `mode:${option.value}` === next);
        if (option && !option.disabled) onValueChange(option.value);
      }}>
      {options.map(option => <ToggleGroupPrimitive.Item key={option.value} value={`mode:${option.value}`}
        data-slot="toggle-group-item" className="mode-toggle-item"
        disabled={option.disabled} title={option.title} aria-label={option.ariaLabel}>
        {value === option.value && <motion.span aria-hidden="true" className="mode-toggle-indicator"
          layoutId={reduce ? undefined : 'active-mode'} initial={false}
          transition={reduce ? { duration: 0 } : uiTransition}/>}
        <span className="mode-toggle-label">{option.label}</span>
      </ToggleGroupPrimitive.Item>)}
    </ToggleGroupPrimitive.Root>
  </LayoutGroup>;
}
