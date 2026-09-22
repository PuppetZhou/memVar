import { useEffect, useRef, useState, type ReactNode } from 'react';
import { AnimatePresence, motion, useAnimate, useIsPresent, type HTMLMotionProps } from 'motion/react';
import { useReducedMotion } from '@/lib/use-reduced-motion';

export const uiTransition = { duration: 0.18, ease: [0.22, 1, 0.36, 1] as const };

/** Animate a whole region; never mount a motion controller per residue or heatmap cell. */
export function Reveal({ children, className }: { children: ReactNode; className?: string }) {
  const reduce = useReducedMotion();
  return <motion.div className={className}
    initial={reduce ? false : { opacity: 0, y: 4 }}
    animate={{ opacity: 1, y: 0 }}
    transition={reduce ? { duration: 0 } : uiTransition}>{children}</motion.div>;
}

type RegionProps = Omit<HTMLMotionProps<'div'>, 'children'> & { children: ReactNode };

/** Keep the same child tree and focus while acknowledging a change of display mode. */
export function ContentTransition({ transitionKey, children, ...props }: RegionProps & { transitionKey: string | number }) {
  const reduce = useReducedMotion();
  const [scope, animate] = useAnimate<HTMLDivElement>();
  const previousKey = useRef(transitionKey);
  useEffect(() => {
    if (previousKey.current === transitionKey) return;
    previousKey.current = transitionKey;
    if (!scope.current || reduce) return;
    const animation = animate(scope.current, { opacity: [0.65, 1] }, uiTransition);
    return () => {
      animation.stop();
      if (scope.current) scope.current.style.opacity = '1';
    };
  }, [transitionKey, reduce, scope, animate]);
  return <motion.div ref={scope} {...props}>{children}</motion.div>;
}

/** Mount on first use, then preserve filters and scroll positions across collapse. */
export function CollapseRegion({ open, children, style, ...props }: RegionProps & { open: boolean }) {
  const reduce = useReducedMotion();
  const [visited, setVisited] = useState(open);
  useEffect(() => { if (open) setVisited(true); }, [open]);
  return <motion.div {...props}
    initial={false}
    animate={{ height: open ? 'auto' : 0, opacity: open ? 1 : 0 }}
    transition={reduce ? { duration: 0 } : uiTransition}
    aria-hidden={!open}
    inert={!open}
    style={{ ...style, overflow: 'hidden' }}>
    {(open || visited) && children}
  </motion.div>;
}

/** A single feedback region, never one motion instance per scientific mark. */
export function SelectionFeedback({ visible, children, ...props }: RegionProps & { visible: boolean }) {
  return <AnimatePresence initial={false}>
    {visible && <SelectionRegion key="selection-feedback" {...props}>{children}</SelectionRegion>}
  </AnimatePresence>;
}

function SelectionRegion({ children, ...props }: RegionProps) {
  const reduce = useReducedMotion();
  const present = useIsPresent();
  return <motion.div {...props}
    initial={reduce ? false : { opacity: 0, height: 0 }}
    animate={{ opacity: 1, height: 'auto' }}
    exit={{ opacity: 0, height: 0, paddingTop: 0, paddingBottom: 0, marginTop: 0, marginBottom: 0 }}
    transition={reduce ? { duration: 0 } : uiTransition}
    inert={!present}
    style={{ ...props.style, overflow: 'hidden' }}>{children}</motion.div>;
}
