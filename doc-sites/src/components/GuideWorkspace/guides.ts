import {translate} from '@docusaurus/Translate';

export type Guide = {
  id: string; mark: string; name: string; purpose: string; title: string;
  description: string; prompt: string; result: string; check: string;
  next: string; setup: string; image?: string; imageAlt?: string; example: string[];
  codexPrompt?: string; codexResult?: string; codexCheck?: string; codexExample?: string[];
};

// Public, authored learning content. The backend derives its roster from the same
// maintained catalog and retrieves only the public English/Korean guide trees.
export const guides: Guide[] = [
  {
    id: 'aws-content-plugin', mark: '01', name: translate({id: 'learn.name.content', message: 'Content'}),
    purpose: translate({id: 'learn.content.purpose', message: 'Turn an idea into something you can show.'}),
    title: translate({id: 'learn.content.title', message: 'Make your first presentation'}),
    description: translate({id: 'learn.content.description', message: 'Go from a short brief to slides you can open, rehearse and share. Start with a small deck, then explore diagrams and workshops.'}),
    prompt: translate({id: 'learn.content.prompt', message: 'Create a 5-slide introduction to Amazon Bedrock for developers. Use English, include one architecture diagram and speaker notes, and show me a local preview before publishing.'}),
    result: translate({id: 'learn.content.result', message: 'An HTML deck with speaker notes and a local preview. The agent should report its validation and content review before publishing.'}),
    check: translate({id: 'learn.content.check', message: 'Open the preview. Advance with the arrow keys, open presenter notes with N, and rehearse each interactive step. Check your actual deck; the screenshot here is a published example.'}),
    next: '/docs/aws-content-plugin/presenter-guide',
    setup: '/docs/aws-content-plugin/installation',
    image: '/img/reactive-presentation/presenter-window.png',
    imageAlt: translate({id: 'learn.content.imageAlt', message: 'Actual Remarp presenter window with current slide, next slide and speaker notes'}),
    example: [translate({id: 'learn.flow.1', message: 'brief'}), translate({id: 'learn.flow.2', message: 'slides + notes'}), translate({id: 'learn.flow.3', message: 'preview'}), translate({id: 'learn.flow.4', message: 'content review'})],
  },
  {
    id: 'co-agent', mark: '02', name: 'Co-agent',
    purpose: translate({id: 'learn.coagent.purpose', message: 'Get a second view on a difficult change.'}),
    title: translate({id: 'learn.coagent.title', message: 'Review a change with your AI peers'}),
    description: translate({id: 'learn.coagent.description', message: 'Check peer readiness, ask for a focused review, and turn concrete findings into the next action.'}),
    prompt: translate({id: 'learn.coagent.prompt', message: 'Use co-agent to check peer readiness, then review my current diff for correctness and missing validation. Report file-specific findings and explain any unavailable reviewer.'}),
    result: translate({id: 'learn.coagent.result', message: 'A synthesized review with concrete findings, affected files and reviewer coverage. The current host chairs; supported peers are Kiro and the opposite host CLI.'}),
    check: translate({id: 'learn.coagent.check', message: 'Verify which peers actually ran. Read the cited code before accepting a finding. Review can disclose solo coverage; consensus and harness need ready peers.'}),
    next: '/docs/co-agent/overview',
    setup: '/docs/co-agent/installation',
    example: [translate({id: 'learn.flow.5', message: 'setup'}), translate({id: 'learn.flow.6', message: 'peer reviews'}), translate({id: 'learn.flow.7', message: 'chair verification'}), translate({id: 'learn.flow.8', message: 'findings'})],
  },
  {
    id: 'project-init', mark: '03', name: translate({id: 'learn.name.init', message: 'Project init'}),
    purpose: translate({id: 'learn.init.purpose', message: 'Give your project a clear starting point.'}),
    title: translate({id: 'learn.init.title', message: 'Make a repository easier to work in'}),
    description: translate({id: 'learn.init.description', message: 'Build project instructions and documentation from the code that is actually there, then keep decisions and runbooks close to the work.'}),
    prompt: translate({id: 'learn.init.prompt', message: 'Use project-init to inspect this repository and prepare project instructions and onboarding documentation for my current host. Preserve existing instructions and show the proposed changes.'}),
    result: translate({id: 'learn.init.result', message: 'Project documentation based on the detected stack, with host-appropriate instructions and a reviewable diff.'}),
    check: translate({id: 'learn.init.check', message: 'Check every setup command against the repository. Review any hook before installing and trusting it; a generated template is not an enabled hook.'}),
    next: '/docs/project-init/overview',
    setup: '/docs/project-init/installation',
    example: [translate({id: 'learn.flow.9', message: 'inspect repository'}), translate({id: 'learn.flow.10', message: 'detect stack'}), translate({id: 'learn.flow.11', message: 'write instructions'}), translate({id: 'learn.flow.12', message: 'review diff'})],
  },
  {
    id: 'aws-ops-plugin', mark: '04', name: translate({id: 'learn.name.ops', message: 'AWS operations'}),
    purpose: translate({id: 'learn.ops.purpose', message: 'Understand a symptom before changing anything.'}),
    title: translate({id: 'learn.ops.title', message: 'Investigate an AWS or EKS issue'}),
    description: translate({id: 'learn.ops.description', message: 'Start with a specific symptom, account and Region. Follow the evidence from triage to a proposed fix.'}),
    prompt: translate({id: 'learn.ops.prompt', message: 'Use aws-ops-plugin for a read-only investigation of my EKS workload. First confirm the AWS profile, Region and cluster with me. Explain the evidence and propose a fix before making changes.'}),
    result: translate({id: 'learn.ops.result', message: 'A scoped investigation with evidence, likely cause and a proposed resolution. The agent may need an installed companion skill for the affected service.'}),
    check: translate({id: 'learn.ops.check', message: 'Confirm the account and Region in the evidence. Distinguish a confirmed cause from a hypothesis, and review every proposed infrastructure change.'}),
    next: '/docs/aws-ops-plugin/overview',
    setup: '/docs/aws-ops-plugin/installation',
    example: [translate({id: 'learn.flow.13', message: 'confirm scope'}), translate({id: 'learn.flow.14', message: 'read evidence'}), translate({id: 'learn.flow.15', message: 'test hypothesis'}), translate({id: 'learn.flow.16', message: 'propose resolution'})],
  },
  {
    id: 'pr-dash', mark: '05', name: translate({id: 'learn.name.pr', message: 'PR dashboard'}),
    purpose: translate({id: 'learn.pr.purpose', message: 'See what is holding up your pull request.'}),
    title: translate({id: 'learn.pr.title', message: 'Check a pull request without losing your place'}),
    description: translate({id: 'learn.pr.description', message: 'See CI checks and review results while you work. Claude Code has a pane; other hosts can request a text status.'}),
    prompt: translate({id: 'learn.pr.prompt', message: 'Use pr-dash to show the current pull request status, CI checks and latest AI review result. Explain what is still waiting and which commit was reviewed.'}),
    result: translate({id: 'learn.pr.result', message: 'A status report for the current repository and pull request. The Claude Code pane is a host-specific feature; Codex provides a read-only status procedure.'}),
    check: translate({id: 'learn.pr.check', message: 'Check the PR number and commit. A green check on an older commit does not establish that the latest change passed. Outside a PR repository the pane may stay quiet.'}),
    next: '/docs/pr-dash/overview',
    setup: '/docs/pr-dash/overview#get-started',
    codexPrompt: translate({id: 'learn.pr.codexPrompt', message: 'Use the installed pr-dash:pr-status skill to report the current pull request, latest commit, CI checks and AI review result as text. Explain any pending or failed checks.'}),
    example: [translate({id: 'learn.flow.17', message: 'current repository'}), translate({id: 'learn.flow.18', message: 'pull request'}), translate({id: 'learn.flow.19', message: 'checks + reviews'}), translate({id: 'learn.flow.20', message: 'next action'})],
  },
  {
    id: 'agent-dash', mark: '06', name: translate({id: 'learn.name.agent', message: 'Agent dashboard'}),
    purpose: translate({id: 'learn.agent.purpose', message: 'Know who is working and who is waiting.'}),
    title: translate({id: 'learn.agent.title', message: 'Follow delegated work at a glance'}),
    description: translate({id: 'learn.agent.description', message: 'The Claude Code dashboard follows agents, their tasks and delegation. Use it during work that already needs multiple agents.'}),
    prompt: translate({id: 'learn.agent.prompt', message: 'Explain how to enable agent-dash in Claude Code and verify its pane. Show how to read task status, delegation and waiting agents using the installed plugin guide.'}),
    result: translate({id: 'learn.agent.result', message: 'A Claude Code view of the current session’s agents and their task states. Installing its Codex procedures does not add a native Codex dashboard pane.'}),
    check: translate({id: 'learn.agent.check', message: 'Look for the current task and its delegating parent. Empty or waiting states are not proof of failure; use the actual session and task result to confirm completion.'}),
    next: '/docs/agent-dash/overview',
    setup: '/docs/agent-dash/overview#get-started',
    codexPrompt: translate({id: 'learn.agent.codexPrompt', message: 'Use the installed agent-dash:agent-status skill to read the Claude Code team roster and task files. Report member names and types, then task status, owner and blocked-by fields. Mark historical tasks and explain which live details these files cannot show.'}),
    codexResult: translate({id: 'learn.agent.codexResult', message: 'A read-only text report of the available agent-team roster and task files. Missing or stale records are disclosed; this does not open a native dashboard pane in Codex.'}),
    codexCheck: translate({id: 'learn.agent.codexCheck', message: 'Check the team name, task status, owner and blocking fields. If no team is running, the procedure should say so. These files do not establish live waits or delegation history.'}),
    codexExample: [
      translate({id: 'learn.agent.flow.roster', message: 'team roster'}),
      translate({id: 'learn.agent.flow.tasks', message: 'task files'}),
      translate({id: 'learn.agent.flow.owner', message: 'status + owner'}),
      translate({id: 'learn.agent.flow.blocks', message: 'blocking fields'}),
    ],
    example: [translate({id: 'learn.flow.21', message: 'current session'}), translate({id: 'learn.flow.22', message: 'parent agent'}), translate({id: 'learn.flow.23', message: 'delegated tasks'}), translate({id: 'learn.flow.24', message: 'waiting + results'})],
  },
];
