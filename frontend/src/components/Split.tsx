import type { ElementType } from 'react'

/**
 * Word-by-word mask reveal, driven by a `data-active` / `.is-in` ancestor.
 * Wrap a word in *asterisks* to set it in italic.
 */
export default function Split({ text, as: Tag = 'span', className = '', delay = 0 }: { text: string; as?: ElementType; className?: string; delay?: number }) {
  const words = text.split(' ')
  return (
    <Tag className={`split ${className}`}>
      <span className="sr-only">{text.replaceAll('*', '')}</span>
      <span aria-hidden="true">
        {words.map((word, i) => {
          const italic = word.startsWith('*')
          const clean = word.replaceAll('*', '')
          return (
            <span key={i}>
              <span className="w">
                <span style={{ '--i': i + delay } as React.CSSProperties} className={italic ? 'italic' : undefined}>
                  {clean}
                </span>
              </span>
              {i < words.length - 1 && ' '}
            </span>
          )
        })}
      </span>
    </Tag>
  )
}
