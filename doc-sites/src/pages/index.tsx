import React from 'react';
import Layout from '@theme/Layout';
import {translate} from '@docusaurus/Translate';
import GuideWorkspace from '../components/GuideWorkspace';

export default function Home() {
  return (
    <Layout title={translate({id: 'learn.pageTitle', message: 'Learn by doing'})}
      description={translate({id: 'learn.pageDescription', message: 'Hands-on learning paths for six Claude Code and Codex plugins. Install, try a first task, and get help from the guide assistant.'})}>
      <GuideWorkspace />
    </Layout>
  );
}
