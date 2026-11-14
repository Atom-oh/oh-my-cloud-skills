import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {BedrockRuntimeClient, ConverseCommand} from '@aws-sdk/client-bedrock-runtime';
import {DynamoDBClient, TransactWriteItemsCommand} from '@aws-sdk/client-dynamodb';
import {CognitoJwtVerifier} from 'aws-jwt-verify';
import {createApp} from './http.mjs';
import {answerQuestion} from './chat.mjs';
import {createQuotaLimiter} from './quota.mjs';

const region = process.env.AWS_REGION || 'us-east-1';
const origin = process.env.SITE_ORIGIN || 'http://127.0.0.1:3000';
const userPoolId = process.env.COGNITO_USER_POOL_ID;
const clientId = process.env.COGNITO_CLIENT_ID;
const domain = process.env.COGNITO_DOMAIN;
const quotaTable = process.env.QUOTA_TABLE;
const authConfigured = Boolean(userPoolId && clientId && domain && quotaTable);
const verifier = authConfigured ? CognitoJwtVerifier.create({userPoolId, tokenUse: 'access', clientId}) : null;
const bedrock = new BedrockRuntimeClient({region, maxAttempts: 2});
const dynamo = new DynamoDBClient({region, maxAttempts: 2});
const corpus = JSON.parse(await readFile(new URL('./content.generated.json', import.meta.url), 'utf8'));
const app = createApp({
  buildDir: fileURLToPath(new URL('./public/', import.meta.url)), origin,
  publicConfig: {chatAvailable: authConfigured, auth: authConfigured ? {
    clientId, domain, redirectUri: `${origin}/`, userPoolId,
  } : null},
  authenticate: async (token) => {
    if (!verifier) throw new Error('Not configured');
    return (await verifier.verify(token)).sub;
  },
  consumeQuota: createQuotaLimiter({
    table: quotaTable,
    dailyLimit: Number(process.env.DAILY_CHAT_LIMIT || 250),
    userLimit: Number(process.env.USER_DAILY_CHAT_LIMIT || 30),
    write: (request, abortSignal) => dynamo.send(new TransactWriteItemsCommand(request), {abortSignal}),
  }),
  answer: (question, signal) => answerQuestion(question, {
    corpus, signal,
    specialistModel: process.env.SPECIALIST_MODEL_ID || 'us.anthropic.claude-haiku-5-5',
    finalModel: process.env.FINAL_MODEL_ID || 'us.openai.gpt-6-luna',
    invoke: async ({modelId, system, prompt, maxTokens, signal: abortSignal}) => {
      const result = await bedrock.send(new ConverseCommand({
        modelId, system: [{text: system}], messages: [{role: 'user', content: [{text: prompt}]}],
        inferenceConfig: {maxTokens},
      }), {abortSignal});
      return (result.output?.message?.content || []).map((part) => part.text || '').join('');
    },
  }),
});
const endpoint = new URL(`http://${process.env.AWS_LAMBDA_HTTP_ENDPOINT || '127.0.0.1:3000'}`);
app.listen(Number(endpoint.port), endpoint.hostname, () => console.log('Guide server ready'));
