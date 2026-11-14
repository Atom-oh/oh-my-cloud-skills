import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const baseUrl = '/';

const config: Config = {
  title: 'oh-my-cloud-skills',
  tagline: 'Cloud workflows for Claude Code and Codex',
  favicon: 'img/logo.svg',

  future: {
    v4: true,
  },

  url: 'https://skills.atomai.click',
  baseUrl,

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
        translate: true,
      },
      en: {
        label: 'English',
        htmlLang: 'en',
        translate: false,
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
          editLocalizedFiles: true,
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
          to: '/',
          position: 'left',
          label: 'Home',
        },
        {
          type: 'dropdown',
          label: 'Plugins',
          position: 'left',
          items: [
            {label: 'co-agent', to: '/?plugin=co-agent'},
            {label: 'project-init', to: '/?plugin=project-init'},
            {label: 'aws-content-plugin', to: '/?plugin=aws-content-plugin'},
            {label: 'aws-ops-plugin', to: '/?plugin=aws-ops-plugin'},
            {label: 'pr-dash', to: '/?plugin=pr-dash'},
            {label: 'agent-dash', to: '/?plugin=agent-dash'},
          ],
        },
        {
          type: 'docSidebar',
          sidebarId: 'remarpGuide',
          position: 'left',
          label: 'Remarp Guide',
        },
        {
          to: '/docs/releases/v2.0.0',
          label: 'Release notes',
          position: 'right',
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
            {label: 'co-agent', to: '/docs/co-agent/overview'},
            {label: 'project-init', to: '/docs/project-init/overview'},
            {label: 'aws-content-plugin', to: '/docs/aws-content-plugin/overview'},
            {label: 'aws-ops-plugin', to: '/docs/aws-ops-plugin/overview'},
            {label: 'pr-dash', to: '/docs/pr-dash/overview'},
            {label: 'agent-dash', to: '/docs/agent-dash/overview'},
          ],
        },
        {
          title: 'Guides',
          items: [
            {label: 'Remarp Guide', to: '/docs/remarp-guide/introduction'},
            {label: 'Getting started', to: '/docs/intro'},
            {label: 'Release notes', to: '/docs/releases/v2.0.0'},
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
