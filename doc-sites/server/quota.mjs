import {createHash, randomUUID} from 'node:crypto';
import {setTimeout} from 'node:timers/promises';

export function createQuotaLimiter({table, dailyLimit, userLimit, write,
  wait = (ms, signal) => setTimeout(ms, undefined, {signal})}) {
  return async (subject, signal) => {
    signal?.throwIfAborted();
    if (!table) return false;
    const day = new Date().toISOString().slice(0, 10);
    const subjectHash = createHash('sha256').update(subject).digest('hex');
    const ttl = Math.floor(Date.now() / 1000) + 172800;
    const request = {
      // Keep this token and the exact transaction stable across ambiguous retries.
      ClientRequestToken: randomUUID(),
      TransactItems: [[`day:${day}`, dailyLimit], [`user:${day}:${subjectHash}`, userLimit]]
        .map(([key, limit]) => ({Update: {
          TableName: table, Key: {id: {S: key}},
          UpdateExpression: 'SET expires = :ttl ADD requests :one',
          ConditionExpression: 'attribute_not_exists(requests) OR requests < :limit',
          ExpressionAttributeValues: {':ttl': {N: String(ttl)}, ':one': {N: '1'}, ':limit': {N: String(limit)}},
        }})),
    };
    for (let attempt = 0; attempt < 4; attempt++) {
      signal?.throwIfAborted();
      try {
        await write(request, signal);
        return true;
      } catch (error) {
        const reasons = error.CancellationReasons || [];
        if (error.name === 'TransactionCanceledException' && reasons.some((r) => r.Code === 'ConditionalCheckFailed')) return false;
        const retryable = error.name === 'TransactionConflictException'
          || error.name === 'TransactionInProgressException'
          || (error.name === 'TransactionCanceledException' && reasons.some((r) => r.Code === 'TransactionConflict'));
        if (!retryable || attempt === 3) throw new Error('Quota service unavailable');
        await wait(50 * 2 ** attempt + Math.floor(Math.random() * 40), signal);
      }
    }
    return false;
  };
}
