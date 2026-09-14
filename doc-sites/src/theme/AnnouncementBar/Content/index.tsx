import type {ComponentProps, ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import Translate from '@docusaurus/Translate';

export default function AnnouncementBarContent(props: ComponentProps<'div'>): ReactNode {
  return (
    <div {...props} className={clsx('release-notice', props.className)}>
      <strong>
        <Translate id="release.notice">v2.0.0 is available.</Translate>
      </strong>{' '}
      <Link to="/docs/releases/v2.0.0">
        <Translate id="release.guide">Release notes and co-agent migration</Translate>
      </Link>
    </div>
  );
}
