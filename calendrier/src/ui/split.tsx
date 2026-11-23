import { Fragment } from 'react';

/** Découpe un texte en lettres animables, en gardant les mots insécables et lisibles par les lecteurs d'écran. */
export function SplitLetters({ text, className = '' }: { text: string; className?: string }) {
  const words = text.split(' ');
  return (
    <span className={className} aria-label={text} role="text">
      {words.map((word, w) => (
        <span className="split-word" aria-hidden="true" key={`${word}-${w}`}>
          {[...word].map((ch, i) => (
            <span className="split-char" key={i}>
              {ch}
            </span>
          ))}
          {w < words.length - 1 ? <span className="split-space">&nbsp;</span> : null}
        </span>
      ))}
    </span>
  );
}

export function SplitWords({ text, className = '' }: { text: string; className?: string }) {
  const words = text.split(' ');
  return (
    <span className={className} aria-label={text} role="text">
      {words.map((word, w) => (
        <Fragment key={`${word}-${w}`}>
          <span className="split-wordmask" aria-hidden="true">
            <span className="split-wordin">{word}</span>
          </span>
          {w < words.length - 1 ? ' ' : null}
        </Fragment>
      ))}
    </span>
  );
}
