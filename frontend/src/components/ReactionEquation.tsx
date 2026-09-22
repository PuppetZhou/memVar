/** Typographic formatting only: preserve source wording and reaction direction. */
export function ReactionEquation({text}:{text:string}) {
  return <div className="reaction-equation" aria-label={text}><span className="reaction-equation-label" aria-hidden="true">Reaction</span><p>{text.split(/(\(\d*[+-]\))/g).map((part,index)=>/^\(\d*[+-]\)$/.test(part)?<sup key={index}>{part.slice(1,-1)}</sup>:<span key={index}>{part}</span>)}</p></div>;
}
