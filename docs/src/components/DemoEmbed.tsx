import React from 'react';

interface DemoEmbedProps {
  title: string;
  src: string;
  height?: number;
  command?: string;
  remarpSource?: string;
}

export default function DemoEmbed({
  title,
  src,
  height = 500,
  command,
  remarpSource,
}: DemoEmbedProps): React.ReactElement {
  return (
    <div className="demo-embed">
      <div className="demo-embed__header">
        <span className="demo-embed__title">{title}</span>
        <span className="demo-embed__actions">
          <a href={src} target="_blank" rel="noopener noreferrer">
            새 탭에서 열기 ↗
          </a>
        </span>
      </div>
      <iframe
        className="demo-embed__iframe"
        src={src}
        style={{height: `${height}px`}}
        title={title}
        loading="lazy"
        sandbox="allow-scripts allow-same-origin"
      />
      {(command || remarpSource) && (
        <div className="demo-embed__footer">
          {command && (
            <div>
              <strong>생성 명령어:</strong> <code>{command}</code>
            </div>
          )}
          {remarpSource && (
            <div style={{marginTop: command ? '0.5rem' : 0}}>
              <strong>Remarp 소스:</strong> <code>{remarpSource}</code>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
