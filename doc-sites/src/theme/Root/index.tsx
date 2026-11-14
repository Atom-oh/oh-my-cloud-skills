import React, {type ReactNode} from 'react';
import GuideChat from '../../components/GuideChat';

export default function Root({children}: {children: ReactNode}) {
  return <>{children}<GuideChat /></>;
}
