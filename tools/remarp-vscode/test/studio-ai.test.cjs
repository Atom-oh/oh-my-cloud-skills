const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'), path=require('node:path'), os=require('node:os');
const {validateAIConfig,aiProvider,aiRequest,prepareAI,aiResponse,startAI}=require('../out/studioAI');
const config=(provider='claude',executable='claude',more={})=>({provider,executable,model:'',effort:'',timeoutSeconds:10,...more});
function temp(){return fs.mkdtempSync(path.join(os.tmpdir(),'studio-ai-test-'));}
function fake(root,body){const file=path.join(root,'fake-cli');fs.writeFileSync(file,`#!${process.execPath}\n${body}`,{mode:0o700});return file;}
test('provider, effort, path and timeout validation rejects shell strings and invalid settings',()=>{
 for(const c of [config('gemini'),config('claude','claude --unsafe'),config('claude','x',{model:'-bad'}),config('codex','codex',{effort:'max'}),config('claude','claude',{timeoutSeconds:0})])assert.throws(()=>validateAIConfig(c));
 assert.throws(()=>aiProvider({provider:'claude'}));assert.equal(validateAIConfig(config('claude','/tmp/path with spaces/claude')).provider,'claude');
});
test('request uses bounded JSON data with notes and Korean text, never executable interpolation',()=>{
 const source='## 소개\n$(touch /tmp/unsafe)\n:::notes\nkeep\n:::\n';
 const p=aiRequest(source,'Improve spacing');assert.deepEqual(JSON.parse(p.slice(p.indexOf('\n')+1)),{request:'Improve spacing',source});
 for(const v of ['',{},'x'.repeat(4001),'a\0b'])assert.throws(()=>aiRequest(source,v));assert.throws(()=>aiRequest('x'.repeat(100001),'ok'));
});
test('Claude disables tools and customizations and takes source only on stdin',()=>{
 const root=temp();try{const p=prepareAI(config('claude','claude',{model:'sonnet',effort:'high'}),'PRIVATE_SOURCE',root);
 assert.ok(p.args.includes('--safe-mode'));assert.ok(p.args.includes('--strict-mcp-config'));assert.equal(p.args[p.args.indexOf('--tools')+1],'');assert.ok(p.args.includes('--no-session-persistence'));
 assert.equal(p.stdin,'PRIVATE_SOURCE');assert.ok(!p.args.join(' ').includes('PRIVATE_SOURCE'));assert.ok(!p.args.some(x=>x.includes('bypass')));
 }finally{fs.rmSync(root,{recursive:true,force:true});}
});
test('Codex is ephemeral read-only with isolated config, tools disabled and provider-specific effort',()=>{
 const root=temp();try{const p=prepareAI(config('codex','codex',{model:'test-model',effort:'xhigh'}),'PRIVATE_SOURCE',root);
 assert.ok(p.args.includes('read-only'));assert.ok(p.args.includes('--ignore-user-config'));assert.ok(p.args.includes('--ignore-rules'));assert.ok(p.args.includes('--ephemeral'));
 assert.ok(p.args.includes('shell_tool'));assert.ok(p.args.includes('hooks'));assert.ok(p.args.includes('model_reasoning_effort="xhigh"'));assert.equal(p.args.at(-1),'-');assert.equal(p.stdin,'PRIVATE_SOURCE');
 assert.ok(!p.args.some(x=>x.includes('dangerously')||x.includes('full-auto')));
 }finally{fs.rmSync(root,{recursive:true,force:true});}
});
test('Kiro supplies private source as a resource, not argv, and grants no tools or MCP',()=>{
 const root=temp();try{const p=prepareAI(config('kiro','kiro-cli',{effort:'low'}),'PRIVATE_SOURCE',root);
 assert.ok(p.args.includes('--trust-tools='));assert.ok(!p.args.some(x=>x.includes('PRIVATE_SOURCE')));assert.equal(p.stdin,'');
 const agent=JSON.parse(fs.readFileSync(path.join(root,'.kiro/agents',fs.readdirSync(path.join(root,'.kiro/agents'))[0])));
 assert.deepEqual(agent.tools,[]);assert.equal(agent.includeMcpJson,false);assert.deepEqual(agent.mcpServers,{});assert.deepEqual(agent.hooks,[]);assert.match(agent.resources[0],/request.txt$/);
 assert.equal(fs.readFileSync(path.join(root,'request.txt'),'utf8'),'PRIVATE_SOURCE');assert.equal(fs.statSync(path.join(root,'request.txt')).mode&0o777,0o600);
 }finally{fs.rmSync(root,{recursive:true,force:true});}
});
test('only final provider text becomes a candidate, not reasoning or tool output',()=>{
 const root=temp();try{
 assert.equal(aiResponse('claude',JSON.stringify({type:'result',result:'```md\n## New\n```'}),root),'## New\n');
 assert.throws(()=>aiResponse('claude',JSON.stringify({type:'result',is_error:true,result:'## Bad'}),root));
 const text=[{params:{update:{sessionUpdate:'agent_thought_chunk',content:{type:'text',text:'hidden'}}}},{params:{update:{sessionUpdate:'agent_message_chunk',content:{type:'text',text:'## 결과'}}}}].concat([{type:'runFinished',data:{status:'success',stopReason:'end_turn'}}]).map(JSON.stringify).join('\n');
 assert.equal(aiResponse('kiro',text,root),'## 결과\n');assert.throws(()=>aiResponse('kiro','banner',root));assert.throws(()=>aiResponse('kiro',text+'\n'+JSON.stringify({error:'failed'}),root));
 fs.writeFileSync(path.join(root,'response.md'),'## Codex');assert.equal(aiResponse('codex','progress text ignored',root),'## Codex\n');
 for(const source of ['','---\nremarp: true\n---\n## New','x'.repeat(100001)])assert.throws(()=>aiResponse('claude',JSON.stringify({type:'result',result:source}),root));
 }finally{fs.rmSync(root,{recursive:true,force:true});}
});
test('runner uses a private scratch cwd, preserves UTF-8, cleans up and never starts a shell',async()=>{
 const root=temp();try{
 const cli=fake(root,`let s='';process.stdin.setEncoding('utf8');process.stdin.on('data',d=>s+=d);process.stdin.on('end',()=>{require('fs').writeFileSync(${JSON.stringify(path.join(root,'cwd'))},process.cwd());require('fs').writeSync(1,JSON.stringify({type:'result',result:'## 한글\\n'+s}));});`);
 const job=startAI(config('claude',cli),'$(touch /tmp/remarp-AI-unsafe)');assert.match(await job.result,/한글/);
 const cwd=fs.readFileSync(path.join(root,'cwd'),'utf8');assert.notEqual(cwd,root);assert.ok(!fs.existsSync(cwd));assert.ok(!fs.existsSync('/tmp/remarp-AI-unsafe'));
 }finally{fs.rmSync(root,{recursive:true,force:true});}
});
test('Codex runner reads the final-message file; Kiro runner reads only ACP message chunks',async()=>{
 const root=temp();try{
 const codex=fake(root,`const a=process.argv;require('fs').writeFileSync(a[a.indexOf('--output-last-message')+1],'## Codex');`);
 assert.equal(await startAI(config('codex',codex),'data').result,'## Codex\n');
 const kiro=fake(root,`require('fs').writeSync(1,[{type:'sessionUpdate',data:{update:{sessionUpdate:'agent_message_chunk',content:{type:'text',text:'## Kiro'}}}},{type:'runFinished',data:{status:'success',stopReason:'end_turn',finalText:'## Kiro',finalTextTruncated:false}}].map(JSON.stringify).join('\\n'));`);
 assert.equal(await startAI(config('kiro',kiro),'data').result,'## Kiro\n');
 }finally{fs.rmSync(root,{recursive:true,force:true});}
});
test('missing CLI and nonzero failure do not expose raw credentials or prompts',async()=>{
 const root=temp();try{
 await assert.rejects(startAI(config('claude',path.join(root,'absent')),'data').result,/could not start/);
 const cli=fake(root,`require('fs').writeSync(2,'SECRET_SOURCE TOKEN=secret not logged in');process.exit(1);`);
 await assert.rejects(startAI(config('claude',cli),'PRIVATE').result,e=>/authentication/.test(e.message)&&!e.message.includes('SECRET')&&!e.message.includes('TOKEN'));
 }finally{fs.rmSync(root,{recursive:true,force:true});}
});
test('Cancel terminates the process group and removes scratch context',async()=>{
 const root=temp();try{
 const mark=path.join(root,'started');const cli=fake(root,`require('fs').writeFileSync(${JSON.stringify(mark)},process.cwd());process.stdin.resume();setInterval(()=>{},1000);`);
 const job=startAI(config('claude',cli),'data');for(let n=0;n<100&&!fs.existsSync(mark);n++)await new Promise(r=>setTimeout(r,10));
 assert.ok(fs.existsSync(mark));job.cancel();await assert.rejects(job.result,/cancelled/);assert.ok(!fs.existsSync(fs.readFileSync(mark,'utf8')));
 }finally{fs.rmSync(root,{recursive:true,force:true});}
});
test('oversized output terminates the CLI rather than buffering unbounded content',async()=>{
 const root=temp();try{const cli=fake(root,`require('fs').writeSync(1,'x'.repeat(3*1024*1024));setInterval(()=>{},1000);`);await assert.rejects(startAI(config('claude',cli),'data').result,/output exceeded/);}finally{fs.rmSync(root,{recursive:true,force:true});}
});
test('timeout kills a nonresponsive CLI without accepting partial output',async()=>{
 const root=temp();try{const cli=fake(root,`require('fs').writeSync(1,'{"type":"result"');process.on('SIGTERM',()=>{});setInterval(()=>{},1000);`);await assert.rejects(startAI(config('claude',cli),'data').result,/timed out/);}finally{fs.rmSync(root,{recursive:true,force:true});}
});
test('Kiro requires a successful completion event and ignores reasoning and truncated final metadata',()=>{
 const root=temp();try{
 const chunk={type:'sessionUpdate',data:{update:{sessionUpdate:'agent_message_chunk',content:{type:'text',text:'## Good'}}}};
 assert.throws(()=>aiResponse('kiro',JSON.stringify(chunk),root),/without a successful/);
 const end={type:'runFinished',data:{status:'success',stopReason:'end_turn',finalText:'## Truncated',finalTextTruncated:true}};
 assert.equal(aiResponse('kiro',[chunk,end].map(JSON.stringify).join('\n'),root),'## Good\n');
 end.data.status='interrupted';assert.throws(()=>aiResponse('kiro',[chunk,end].map(JSON.stringify).join('\n'),root));
 }finally{fs.rmSync(root,{recursive:true,force:true});}
});
test('Codex response rejects symlinks and non-regular files without reading them',()=>{
 const root=temp();try{const file=path.join(root,'response.md');fs.mkdirSync(file);assert.throws(()=>aiResponse('codex','',root),/bounded/);fs.rmdirSync(file);fs.symlinkSync('/dev/null',file);assert.throws(()=>aiResponse('codex','',root),/bounded/);}finally{fs.rmSync(root,{recursive:true,force:true});}
});
test('POSIX cancellation kills an inherited child process as well as its parent',async()=>{
 if(process.platform==='win32')return;
 const root=temp();try{
 const started=path.join(root,'started'),late=path.join(root,'late');
 const cli=fake(root,`require('child_process').spawn('/usr/bin/python3',['-c',${JSON.stringify(`import time,pathlib;time.sleep(1);pathlib.Path(${JSON.stringify(late)}).write_text('late')`)}],{stdio:'ignore'});require('fs').writeFileSync(${JSON.stringify(started)},'yes');process.stdin.resume();setInterval(()=>{},1000);`);
 const job=startAI(config('claude',cli),'data');for(let n=0;n<100&&!fs.existsSync(started);n++)await new Promise(r=>setTimeout(r,10));assert.ok(fs.existsSync(started));
 job.cancel();await assert.rejects(job.result,/cancelled/);await new Promise(r=>setTimeout(r,1200));assert.ok(!fs.existsSync(late));
 }finally{fs.rmSync(root,{recursive:true,force:true});}
});
