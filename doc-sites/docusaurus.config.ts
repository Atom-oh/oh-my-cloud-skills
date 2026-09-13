import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'oh-my-cloud-skills',
  tagline: 'Cloud workflows for Claude Code and Codex',
  favicon: 'img/logo.svg',

  future: {
    v4: true,
  },

  url: 'https://www.atomai.click',
  baseUrl: '/oh-my-cloud-skills/',

  organizationName: 'Atom-oh',
  projectName: 'oh-my-cloud-skills',

  onBrokenLinks: 'throw',

  markdown: {
    mermaid: true,
  },
  themes: ['@docusaurus/theme-mermaid'],

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
    localeConfigs: {
      en: {
        label: 'English',
        htmlLang: 'en',
      },
    },
  },

  plugins: ['./plugins/legacy-locales.cjs'],

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl:
            'https://github.com/Atom-oh/oh-my-cloud-skills/tree/main/doc-sites/',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
        gtag: {
          trackingID: 'G-GWVLEW5JLL',
          anonymizeIP: true,
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
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
          type: 'dropdown',
          label: 'Plugins',
          position: 'left',
          items: [
            {label: 'co-agent', to: '/docs/co-agent/overview'},
            {label: 'kiro', to: '/docs/kiro/overview'},
            {label: 'atlas', to: '/docs/atlas/overview'},
            {label: 'project-init', to: '/docs/project-init/overview'},
            {label: 'aws-content-plugin', to: '/docs/aws-content-plugin/overview'},
            {label: 'aws-ops-plugin', to: '/docs/aws-ops-plugin/overview'},
            {label: 'kiro-power-converter', to: '/docs/kiro-power-converter/overview'},
            {label: 'agentcore-creator', to: '/docs/agentcore-creator/overview'},
          ],
        },
        {
          type: 'docSidebar',
          sidebarId: 'remarpGuide',
          position: 'left',
          label: 'Remarp Guide',
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
            {label: 'co-agent', to: '/docs/co-agent/overview'},
            {label: 'kiro', to: '/docs/kiro/overview'},
            {label: 'atlas', to: '/docs/atlas/overview'},
            {label: 'project-init', to: '/docs/project-init/overview'},
            {label: 'aws-content-plugin', to: '/docs/aws-content-plugin/overview'},
            {label: 'aws-ops-plugin', to: '/docs/aws-ops-plugin/overview'},
            {label: 'kiro-power-converter', to: '/docs/kiro-power-converter/overview'},
            {label: 'agentcore-creator', to: '/docs/agentcore-creator/overview'},
          ],
        },
        {
          title: 'Guides',
          items: [
            {label: 'Remarp Guide', to: '/docs/remarp-guide/introduction'},
            {label: 'Getting started', to: '/docs/intro'},
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
