// Shared start/final publication guards. Called only by the trusted-base workflow.
const fs = require('fs');
const path = require('path');

module.exports = async function publish({github, context, core, phase}) {
  const marker = '<!-- oh-my-cloud-skills-pr-review -->';
  const head = process.env.REVIEW_HEAD;
  const baseRef = process.env.REVIEW_BASE_REF;
  const run = String(context.runId);
  const attempt = process.env.GITHUB_RUN_ATTEMPT || '1';
  if (!/^[0-9a-f]{40}$/.test(head || '') || !baseRef ||
      !/^[0-9]+$/.test(run) || !/^[1-9][0-9]*$/.test(attempt) ||
      !['pending', 'final'].includes(phase)) throw new Error('Invalid review publication identity');
  const stamp = `<!-- review-run: ${run}/${attempt} -->`;
  const comments = await github.paginate(github.rest.issues.listComments,
    {...context.repo, issue_number: context.issue.number, per_page: 100});
  const existing = comments.filter(c => c.user?.login === 'github-actions[bot]' &&
    typeof c.body === 'string' && c.body.startsWith(marker))
    .sort((a, b) => a.updated_at.localeCompare(b.updated_at)).pop();
  const previous = existing?.body.match(/^<!-- review-run: ([0-9]+)\/([0-9]+) -->$/m);
  const newer = previous && (BigInt(previous[1]) > BigInt(run) ||
    (BigInt(previous[1]) === BigInt(run) && BigInt(previous[2]) > BigInt(attempt)));
  const pr = await github.rest.pulls.get({...context.repo, pull_number: context.issue.number});
  if (newer || pr.data.head.sha !== head || pr.data.base.ref !== baseRef) {
    core.setFailed('Review head, target branch, or run is stale; no comment was overwritten.');
    return;
  }
  const footer = `_Triggered by commit \`${head}\` · workflow: \`.github/workflows/pr-review.yml\`_`;
  let body;
  if (phase === 'pending') {
    body = [marker, stamp, '## AI Code Review', '**Status: PENDING**',
      'Review is running for this HEAD. Previous review text remains in GitHub edit history.',
      '---', footer].join('\n\n');
  } else {
    const expected = {pass: 'PASSED', fail: 'BLOCKED', error: 'ERROR'}[process.env.GATE_RESULT];
    try {
      if (process.env.COMMENT_OUTCOME !== 'success' || !expected ||
          !path.isAbsolute(process.env.pr_work_dir || '')) throw new Error('No completed comment');
      body = fs.readFileSync(path.join(process.env.pr_work_dir, 'comment.md'), 'utf8');
      if (!body.startsWith(marker + '\n') || !body.trimEnd().endsWith(footer) ||
          body.match(/^\*\*Status: (PASSED|BLOCKED|ERROR)\*\*/m)?.[1] !== expected) {
        throw new Error('Comment does not match this review');
      }
      body = body.replace(marker, marker + '\n' + stamp);
    } catch (_) {
      body = [marker, stamp, '## AI Code Review', '**Status: ERROR**',
        'Review did not produce a complete, consistent result. Inspect this run and retry after fixing it.',
        '---', footer].join('\n\n');
      core.setFailed('No publishable review result');
    }
  }
  if (existing) {
    await github.rest.issues.updateComment({...context.repo, comment_id: existing.id, body});
  } else {
    await github.rest.issues.createComment({...context.repo, issue_number: context.issue.number, body});
  }
};
