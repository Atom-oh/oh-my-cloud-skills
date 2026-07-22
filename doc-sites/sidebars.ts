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
        'aws-content-plugin/agents/reactive-presentation-agent',
        'aws-content-plugin/agents/architecture-diagram-agent',
        'aws-content-plugin/agents/animated-diagram-agent',
        'aws-content-plugin/agents/document-agent',
        'aws-content-plugin/agents/gitbook-agent',
        'aws-content-plugin/agents/workshop-agent',
        'aws-content-plugin/agents/brochure-agent',
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
        'aws-content-plugin/skills/slide-fix',
        'aws-content-plugin/skills/gitbook',
        'aws-content-plugin/skills/workshop-creator',
        'aws-content-plugin/skills/brochure',
        'aws-content-plugin/skills/gh-home',
        'aws-content-plugin/skills/aws-light-fcd',
      ],
    },
    {
      type: 'category',
      label: 'Demos',
      items: [
        'aws-content-plugin/demos/full-presentation-demo',
        'aws-content-plugin/demos/bedrock-first-calldeck',
        'aws-content-plugin/demos/basic-presentation',
        'aws-content-plugin/demos/canvas-animation',
        'aws-content-plugin/demos/quiz-slides',
        'aws-content-plugin/demos/compare-tabs',
        'aws-content-plugin/demos/architecture-diagram-demo',
        'aws-content-plugin/demos/animated-diagram-demo',
        'aws-content-plugin/demos/workshop-demo',
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
        'aws-ops-plugin/agents/wellarchitected-agent',
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
        'aws-ops-plugin/skills/ops-wellarchitected-review',
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
        'aws-ops-plugin/demos/health-check-demo',
        'aws-ops-plugin/demos/network-diagnosis-demo',
        'aws-ops-plugin/demos/security-audit-demo',
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

  agentcoreCreator: [
    'agentcore-creator/overview',
    'agentcore-creator/installation',
    'agentcore-creator/agents/agentcore-creator-agent',
    'agentcore-creator/skills/agentcore-create',
  ],

  coAgent: [
    'co-agent/overview',
    'co-agent/installation',
    'co-agent/usage-guide',
    'co-agent/agents/co-agent',
    'co-agent/skills/co-agent',
    'co-agent/commands/commands',
  ],

  kiro: [
    'kiro/overview',
    'kiro/installation',
    'kiro/usage-guide',
    'kiro/agents/kiro-delegate-agent',
    'kiro/skills/kiro-delegate',
    'kiro/commands/commands',
  ],

  projectInit: [
    'project-init/overview',
    'project-init/installation',
    'project-init/agents/doc-sync-checker',
    'project-init/skills/project-scaffolder',
    'project-init/skills/pr-autofix',
    'project-init/skills/decision-reconcile',
    'project-init/commands/commands',
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
    'remarp-guide/workflow',
    'remarp-guide/build-cli',
    'remarp-guide/vscode-extension',
    'remarp-guide/migration-from-marp',
    'remarp-guide/keyboard-shortcuts',
    {
      type: 'category',
      label: 'Examples',
      items: [
        'remarp-guide/examples/basic-example',
        'remarp-guide/examples/canvas-example',
        'remarp-guide/examples/data-viz-example',
      ],
    },
  ],
};

export default sidebars;
