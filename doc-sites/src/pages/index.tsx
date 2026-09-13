import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import styles from './index.module.css';

const plugins = [
  {
    "title": "co-agent",
    "description": "Peer review, decision support, ADRs, and verified implementation pipelines.",
    "link": "/docs/co-agent/overview"
  },
  {
    "title": "kiro",
    "description": "Kiro implementation and optional review, with host-owned plans and verification.",
    "link": "/docs/kiro/overview"
  },
  {
    "title": "atlas",
    "description": "A repository wiki with coverage metadata and git-based documentation drift checks.",
    "link": "/docs/atlas/overview"
  },
  {
    "title": "project-init",
    "description": "Project setup, instructions, ADRs, runbooks, and documentation maintenance for both hosts.",
    "link": "/docs/project-init/overview"
  },
  {
    "title": "aws-content-plugin",
    "description": "Web and PowerPoint decks, architecture diagrams, workshops, brochures, and profiles.",
    "link": "/docs/aws-content-plugin/overview"
  },
  {
    "title": "aws-ops-plugin",
    "description": "AWS and EKS diagnostics across infrastructure, security, observability, and cost.",
    "link": "/docs/aws-ops-plugin/overview"
  },
  {
    "title": "kiro-power-converter",
    "description": "Convert plugin sources and skills into Kiro Powers with steering, hooks, and MCP settings.",
    "link": "/docs/kiro-power-converter/overview"
  },
  {
    "title": "agentcore-creator",
    "description": "Design and test agents, then prepare AgentCore harness or Runtime deployments.",
    "link": "/docs/agentcore-creator/overview"
  }
];

function PluginCard({title, description, link}: typeof plugins[0]) {
  return (
    <div className="col col--4">
      <Link to={link} style={{textDecoration: 'none', color: 'inherit'}}>
        <div className="plugin-card">
          <div className="plugin-card__title">{title}</div>
          <div className="plugin-card__description">{description}</div>
        </div>
      </Link>
    </div>
  );
}

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className="hero__title">
          {siteConfig.title}
        </Heading>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
        <div className={styles.buttons}>
          <Link
            className="button button--secondary button--lg"
            to="/docs/intro">
            Get started
          </Link>
          <Link
            className="button button--outline button--lg"
            to="/docs/remarp-guide/introduction"
            style={{marginLeft: '1rem', color: 'white', borderColor: 'rgba(255,255,255,0.5)'}}>
            Remarp Guide
          </Link>
        </div>
      </div>
    </header>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title="Home"
      description={siteConfig.tagline}>
      <HomepageHeader />
      <main>
        <section style={{padding: '3rem 0'}}>
          <div className="container">
            <div className="row">
              {plugins.map((plugin) => (
                <PluginCard key={plugin.title} {...plugin} />
              ))}
            </div>
          </div>
        </section>
        <section style={{padding: '2rem 0 4rem'}}>
          <div className="container">
            <div className="row">
              <div className="col col--8 col--offset-2" style={{textAlign: 'center'}}>
                <Heading as="h2">Claude Code and Codex plugins</Heading>
                <p style={{fontSize: '1.1rem', color: 'var(--ifm-font-color-secondary)'}}>
                  Choose the plugins you need, install them in your host, and request
                  a workflow in plain English. The guide explains setup, verification,
                  and the boundaries of each integration.
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
