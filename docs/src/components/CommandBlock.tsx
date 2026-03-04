import React from 'react';

interface CommandBlockProps {
  title?: string;
  command: string;
  output?: string;
}

export default function CommandBlock({
  title = 'Terminal',
  command,
  output,
}: CommandBlockProps): React.ReactElement {
  return (
    <div className="command-block">
      <div className="command-block__header">
        {title}
      </div>
      <div className="command-block__body">
        <div style={{color: 'var(--ifm-color-primary)'}}>$ {command}</div>
        {output && (
          <div style={{
            marginTop: '0.5rem',
            color: 'var(--ifm-font-color-secondary)',
            whiteSpace: 'pre-wrap',
          }}>
            {output}
          </div>
        )}
      </div>
    </div>
  );
}
