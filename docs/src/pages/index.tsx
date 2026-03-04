import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import styles from './index.module.css';

const plugins = [
  {
    title: 'aws-content-plugin',
    description: '프레젠테이션, 아키텍처 다이어그램, 애니메이션 다이어그램, 문서, GitBook, 워크샵 콘텐츠를 생성합니다.',
    agents: 7,
    skills: 5,
    link: '/docs/aws-content-plugin/overview',
  },
  {
    title: 'aws-ops-plugin',
    description: 'EKS 클러스터 관리, 네트워크 진단, IAM/RBAC, 옵저버빌리티, 스토리지, 데이터베이스, 비용 최적화를 지원합니다.',
    agents: 8,
    skills: 5,
    link: '/docs/aws-ops-plugin/overview',
  },
  {
    title: 'kiro-power-converter',
    description: 'Claude Code 플러그인을 Kiro Power 포맷으로 변환합니다. GitHub URL, 로컬 경로, 마켓플레이스 이름을 지원합니다.',
    agents: 1,
    skills: 1,
    link: '/docs/kiro-power-converter/overview',
  },
];

function PluginCard({title, description, agents, skills, link}: typeof plugins[0]) {
  return (
    <div className={clsx('col col--4')}>
      <Link to={link} style={{textDecoration: 'none', color: 'inherit'}}>
        <div className="plugin-card">
          <div className="plugin-card__title">{title}</div>
          <div className="plugin-card__description">{description}</div>
          <div className="plugin-card__stats">
            <span>{agents} Agents</span>
            <span>{skills} Skills</span>
          </div>
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
            시작하기
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
                <Heading as="h2">Claude Code Plugin Marketplace</Heading>
                <p style={{fontSize: '1.1rem', color: 'var(--ifm-font-color-secondary)'}}>
                  <code>/plugin marketplace add aws-content-plugin</code> 명령어 하나로 설치하고,
                  자연어로 AWS 콘텐츠를 생성하거나 인프라를 운영하세요.
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
