import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  intro: [
    'intro',
  ],

  awsContent: [
    'aws-content-plugin/overview',
    'aws-content-plugin/usage-guide',
    'aws-content-plugin/installation',
    {
      type: 'category',
      label: 'Agents',
      items: [
        'aws-content-plugin/agents/presentation-agent',
        'aws-content-plugin/agents/architecture-diagram-agent',
        'aws-content-plugin/agents/animated-diagram-agent',
        'aws-content-plugin/agents/document-agent',
        'aws-content-plugin/agents/gitbook-agent',
        'aws-content-plugin/agents/workshop-agent',
        'aws-content-plugin/agents/content-review-agent',
      ],
    },
    {
      type: 'category',
      label: 'Skills',
      items: [
        'aws-content-plugin/skills/reactive-presentation',
        'aws-content-plugin/skills/architecture-diagram',
        'aws-content-plugin/skills/animated-diagram',
        'aws-content-plugin/skills/gitbook',
        'aws-content-plugin/skills/workshop-creator',
      ],
    },
    {
      type: 'category',
      label: 'Demos',
      items: [
        'aws-content-plugin/demos/full-presentation-demo',
        'aws-content-plugin/demos/basic-presentation',
        'aws-content-plugin/demos/canvas-animation',
        'aws-content-plugin/demos/quiz-slides',
        'aws-content-plugin/demos/compare-tabs',
      ],
    },
  ],

  awsOps: [
    'aws-ops-plugin/overview',
    'aws-ops-plugin/installation',
    {
      type: 'category',
      label: 'Agents',
      items: [
        'aws-ops-plugin/agents/eks-agent',
        'aws-ops-plugin/agents/network-agent',
        'aws-ops-plugin/agents/iam-agent',
        'aws-ops-plugin/agents/observability-agent',
        'aws-ops-plugin/agents/storage-agent',
        'aws-ops-plugin/agents/database-agent',
        'aws-ops-plugin/agents/cost-agent',
        'aws-ops-plugin/agents/analytics-agent',
        'aws-ops-plugin/agents/ops-coordinator-agent',
      ],
    },
    {
      type: 'category',
      label: 'Skills',
      items: [
        'aws-ops-plugin/skills/ops-troubleshoot',
        'aws-ops-plugin/skills/ops-health-check',
        'aws-ops-plugin/skills/ops-network-diagnosis',
        'aws-ops-plugin/skills/ops-observability',
        'aws-ops-plugin/skills/ops-security-audit',
      ],
    },
    {
      type: 'category',
      label: 'MCP Servers',
      items: [
        'aws-ops-plugin/mcp/mcp-servers',
      ],
    },
    {
      type: 'category',
      label: 'Demos',
      items: [
        'aws-ops-plugin/demos/eks-troubleshooting',
        'aws-ops-plugin/demos/incident-response',
      ],
    },
  ],

  kiroConverter: [
    'kiro-power-converter/overview',
    'kiro-power-converter/installation',
    'kiro-power-converter/agents/kiro-converter-agent',
    'kiro-power-converter/skills/kiro-convert',
    'kiro-power-converter/demos/conversion-example',
  ],

  remarpGuide: [
    'remarp-guide/introduction',
    'remarp-guide/quick-start',
    {
      type: 'category',
      label: 'Syntax Reference',
      items: [
        'remarp-guide/syntax/frontmatter',
        'remarp-guide/syntax/directives',
        'remarp-guide/syntax/fragments',
        'remarp-guide/syntax/layouts',
        'remarp-guide/syntax/canvas-dsl',
        'remarp-guide/syntax/speaker-notes',
        'remarp-guide/syntax/code-blocks',
      ],
    },
    {
      type: 'category',
      label: 'Slide Types',
      items: [
        'remarp-guide/slide-types/content',
        'remarp-guide/slide-types/compare',
        'remarp-guide/slide-types/canvas',
        'remarp-guide/slide-types/quiz',
        'remarp-guide/slide-types/tabs',
        'remarp-guide/slide-types/timeline',
        'remarp-guide/slide-types/checklist',
      ],
    },
    {
      type: 'category',
      label: 'Themes',
      items: [
        'remarp-guide/themes/pptx-extraction',
        'remarp-guide/themes/css-variables',
        'remarp-guide/themes/custom-themes',
      ],
    },
    'remarp-guide/build-cli',
    'remarp-guide/vscode-extension',
    'remarp-guide/migration-from-marp',
    'remarp-guide/keyboard-shortcuts',
    {
      type: 'category',
      label: 'Examples',
      items: [
        'remarp-guide/examples/basic-example',
      ],
    },
  ],
};

export default sidebars;
