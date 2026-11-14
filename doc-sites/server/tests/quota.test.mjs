import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createQuotaLimiter} from '../quota.mjs';

const conflict = () => Object.assign(new Error('conflict'), {name: 'TransactionCanceledException',
  CancellationReasons: [{Code: 'TransactionConflict'}]});
test('retries contention with the same atomic transaction and idempotency token', async () => {
  const requests = [], waits = [];
  const consume = createQuotaLimiter({table: 'quota', dailyLimit: 250, userLimit: 30,
    write: async (request) => { requests.push(request); if (requests.length < 3) throw conflict(); },
    wait: async (delay) => waits.push(delay),
  });
  assert.equal(await consume('subject'), true);
  assert.equal(requests.length, 3);
  assert.equal(new Set(requests.map((r) => r.ClientRequestToken)).size, 1);
  assert.equal(requests[0].TransactItems.length, 2);
  assert.equal(waits.length, 2);
});
test('reports actual limit exhaustion without retrying and bounds conflict retries', async () => {
  let calls = 0;
  const exhausted = createQuotaLimiter({table: 'quota', dailyLimit: 1, userLimit: 1,
    write: async () => {calls++; throw Object.assign(new Error(), {name: 'TransactionCanceledException',
      CancellationReasons: [{Code: 'ConditionalCheckFailed'}]});},
  });
  assert.equal(await exhausted('subject'), false); assert.equal(calls, 1);
  calls = 0;
  const busy = createQuotaLimiter({table: 'quota', dailyLimit: 250, userLimit: 30,
    write: async () => {calls++; throw conflict();}, wait: async () => {},
  });
  await assert.rejects(busy('subject'), /unavailable/);
  assert.equal(calls, 4);
});
test('fails closed on storage failure and respects cancellation', async () => {
  let calls = 0;
  const consume = createQuotaLimiter({table: 'quota', dailyLimit: 250, userLimit: 30,
    write: async () => {calls++; throw new Error('unavailable');},
  });
  await assert.rejects(consume('subject'), /unavailable/);
  assert.equal(calls, 1);
  const abort = new AbortController(); abort.abort();
  await assert.rejects(consume('subject', abort.signal));
  assert.equal(calls, 1);
});
