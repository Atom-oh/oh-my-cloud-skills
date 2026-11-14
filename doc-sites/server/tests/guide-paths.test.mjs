import {test} from 'node:test';
import assert from 'node:assert/strict';
import {guideUrl} from '../guide-paths.mjs';

test('command guide citations use the actual Docusaurus route', () => {
  assert.equal(guideUrl('co-agent/commands/commands', 'en'), '/en/docs/co-agent/commands');
  assert.equal(guideUrl('project-init/commands/commands', 'ko'), '/docs/project-init/commands');
  assert.equal(guideUrl('aws-content-plugin/presenter-guide', 'ko'), '/docs/aws-content-plugin/presenter-guide');
  assert.equal(guideUrl('remarp-guide/slide-types/tabs', 'en'), '/en/docs/remarp-guide/slide-types/tabs');
});
