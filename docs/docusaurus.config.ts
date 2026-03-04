import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'oh-my-cloud-skills',
  tagline: 'AWS 클라우드 작업을 위한 Claude Code 플러그인 마켓플레이스',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'https://atom-oh.github.io',
  baseUrl: '/oh-my-cloud-skills/',

  organizationName: 'Atom-oh',
  projectName: 'oh-my-cloud-skills',

  onBrokenLinks: 'throw',

  markdown: {
    mermaid: true,
  },
  themes: ['@docusaurus/theme-mermaid'],

  i18n: {
    defaultLocale: 'ko',
    locales: ['ko', 'en'],
    localeConfigs: {
      ko: {
        label: '한국어',
        htmlLang: 'ko',
      },
      en: {
        label: 'English',
        htmlLang: 'en',
      },
    },
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl:
            'https://github.com/Atom-oh/oh-my-cloud-skills/tree/main/docs/',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/og-image.png',
    colorMode: {
      defaultMode: 'dark',
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'oh-my-cloud-skills',
      logo: {
        alt: 'oh-my-cloud-skills Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'intro',
          position: 'left',
          label: 'Home',
        },
        {
          type: 'docSidebar',
          sidebarId: 'awsContent',
          position: 'left',
          label: 'aws-content-plugin',
        },
        {
          type: 'docSidebar',
          sidebarId: 'awsOps',
          position: 'left',
          label: 'aws-ops-plugin',
        },
        {
          type: 'docSidebar',
          sidebarId: 'kiroConverter',
          position: 'left',
          label: 'kiro-power-converter',
        },
        {
          type: 'docSidebar',
          sidebarId: 'remarpGuide',
          position: 'left',
          label: 'Remarp Guide',
        },
        {
          type: 'localeDropdown',
          position: 'right',
        },
        {
          href: 'https://github.com/Atom-oh/oh-my-cloud-skills',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Plugins',
          items: [
            {label: 'aws-content-plugin', to: '/docs/aws-content-plugin/overview'},
            {label: 'aws-ops-plugin', to: '/docs/aws-ops-plugin/overview'},
            {label: 'kiro-power-converter', to: '/docs/kiro-power-converter/overview'},
          ],
        },
        {
          title: 'Guides',
          items: [
            {label: 'Remarp Guide', to: '/docs/remarp-guide/introduction'},
            {label: '시작하기', to: '/docs/intro'},
          ],
        },
        {
          title: 'Links',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/Atom-oh/oh-my-cloud-skills',
            },
            {
              label: 'Claude Code',
              href: 'https://claude.ai/code',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Atom-oh. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['bash', 'yaml', 'json', 'python', 'typescript', 'markdown'],
    },
    mermaid: {
      theme: {light: 'neutral', dark: 'dark'},
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
