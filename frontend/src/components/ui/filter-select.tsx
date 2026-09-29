import { useId } from 'react';
import { Check, ChevronDown, ChevronUp } from 'lucide-react';
import { Select } from 'radix-ui';

type Choice = { value: string; label: string };

/** Keep source values intact, including the empty value used for “All”. */
export function FilterSelect({ label, value, onChange, choices }: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  choices: Choice[];
}) {
  const id = useId();
  return <div className="filter">
    <label htmlFor={id}>{label}</label>
    <Select.Root value={`filter:${value}`} onValueChange={next => onChange(next.slice('filter:'.length))}>
      <Select.Trigger id={id} className="filter-select-trigger" aria-label={label}>
        <Select.Value placeholder="Choose…"/>
        <Select.Icon asChild><ChevronDown size={15} aria-hidden="true"/></Select.Icon>
      </Select.Trigger>
      <Select.Portal>
        <Select.Content className="filter-select-content" position="popper" sideOffset={6} collisionPadding={12}>
          <Select.ScrollUpButton className="filter-select-scroll"><ChevronUp size={14}/></Select.ScrollUpButton>
          <Select.Viewport className="filter-select-viewport">
            {choices.map(choice => <Select.Item className="filter-select-option" key={choice.value} value={`filter:${choice.value}`}>
              <Select.ItemText>{choice.label}</Select.ItemText>
              <Select.ItemIndicator className="filter-select-check"><Check size={15}/></Select.ItemIndicator>
            </Select.Item>)}
          </Select.Viewport>
          <Select.ScrollDownButton className="filter-select-scroll"><ChevronDown size={14}/></Select.ScrollDownButton>
        </Select.Content>
      </Select.Portal>
    </Select.Root>
  </div>;
}
