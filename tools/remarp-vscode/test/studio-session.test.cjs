const { test, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const Module = require('node:module');
let configValues = {};
let root, docs, changes, received, messages, applies, diffs, clipboard, sessions, listening, attempts, revealed;
const disposable = () => ({dispose(){}});
const uri = file => ({fsPath:file,scheme:'file',toString:()=>`file://${file}`});
class Range { constructor(start,end){this.start=start;this.end=end;} }
class Selection extends Range {}
const vscode = {
    Uri:{file:uri,joinPath:(base,...parts)=>uri(path.join(base.fsPath,...parts)),parse:s=>({toString:()=>s})}, Range,Selection,
    RelativePattern:class{}, ViewColumn:{Beside:2},
    WorkspaceEdit:class { edits=[]; replace(uri,range,text){this.edits.push({uri,range,text});} },
    commands:{executeCommand:async(...args)=>diffs.push(args)},
    env:{clipboard:{writeText:async s=>{clipboard=s;}}},
    workspace:{isTrusted:true,getConfiguration:()=>({get:(key,fallback)=>configValues[key] ?? fallback}),onDidChangeConfiguration:disposable,get textDocuments(){return [...docs.values()];},
        onDidChangeTextDocument:fn=>{changes.push(fn);return disposable();},
        createFileSystemWatcher:()=>({dispose(){},onDidChange:disposable,onDidCreate:disposable,onDidDelete:disposable}),
        openTextDocument:async file=>docs.get(file.fsPath)||makeDoc(file.fsPath,fs.readFileSync(file.fsPath,'utf8')),
        applyEdit:async edit=>{
            applies.push(edit);
            const grouped=new Map();for(const p of edit.edits){if(!grouped.has(p.uri.fsPath))grouped.set(p.uri.fsPath,[]);grouped.get(p.uri.fsPath).push(p);}
            for(const [file,patches]of grouped){const d=docs.get(file);for(const p of patches.sort((a,b)=>b.range.start-a.range.start))d.text=d.text.slice(0,p.range.start)+p.text+d.text.slice(p.range.end);d.version++;d.isDirty=true;changes.forEach(fn=>fn({document:d}));}
            return true;
        }},
    window:{createWebviewPanel:()=>({dispose(){},onDidDispose:disposable,webview:{html:'',cspSource:'https://resources.example',
        asWebviewUri:f=>({toString:()=>`https://resources.example${encodeURI(f.fsPath)}`}),
        onDidReceiveMessage:fn=>{received=fn;return disposable();},postMessage:async m=>{attempts.push(m);if(listening)messages.push(m);return listening;}}}),
        showTextDocument:async d=>{revealed.push(d);return {document:d,selection:undefined,revealRange(){}};}}
};
const load=Module._load;Module._load=function(name,...args){return name==='vscode'?vscode:load.call(this,name,...args);};
const {StudioSession}=require('../out/studio');
Module._load=load;
const compiler=path.resolve(__dirname,'../../../plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py');
const source='---\nremarp: true\nratio: "16:9"\n---\n@type: cards\n## Compare options\n### Card one\nFirst body\n### Card two\nSecond body\n';
function makeDoc(file,text){const d={fileName:file,uri:uri(file),text,version:1,isDirty:true,languageId:'remarp',getText(){return this.text;},positionAt:o=>o};docs.set(file,d);return d;}
async function waitFor(type,after=0){for(let n=0;n<200;n++){const m=messages.slice(after).find(m=>m.type===type);if(m)return m;await new Promise(r=>setTimeout(r,10));}throw new Error(`No ${type}: ${JSON.stringify(messages.map(({frameHtml,...m})=>m))}`);}
async function open(){const d=makeDoc(path.join(root,'deck.remarp.md'),source);fs.writeFileSync(d.fileName,'OLD DISK SOURCE');const session=new StudioSession(uri(path.resolve(__dirname,'..')),d,compiler);sessions.push(session);return {session,d,built:await waitFor('compiled')};}
async function send(session,message){received(message);await session.messages;}
beforeEach(()=>{configValues={};root=fs.mkdtempSync(path.join(os.tmpdir(),'studio-session-'));docs=new Map();changes=[];messages=[];applies=[];diffs=[];sessions=[];clipboard='';listening=true;attempts=[];revealed=[];vscode.workspace.isTrusted=true;});
afterEach(async()=>{sessions.forEach(s=>s.dispose());await new Promise(r=>setTimeout(r,20));fs.rmSync(root,{recursive:true,force:true});});
test('Studio compiles unsaved snapshots without saving or touching published output',async()=>{
    const {d,built}=await open();assert.equal(fs.readFileSync(d.fileName,'utf8'),'OLD DISK SOURCE');
    assert.ok(!fs.existsSync(path.join(root,'slides')));assert.equal(built.manifest.slides[0].title,'Compare options');
    const frame=built.frameHtml;
    assert.match(frame,/Compare options/);assert.doesNotMatch(frame,/acquireVsCodeApi/);
});
test('Studio builds when the system temporary directory sits behind a symlink (the macOS default)',async()=>{
    const real=fs.mkdtempSync(path.join(os.tmpdir(),'studio-realtmp-')),link=real+'-link',saved=process.env.TMPDIR;
    fs.symlinkSync(real,link);process.env.TMPDIR=link;
    try{const {built}=await open();assert.equal(built.manifest.slides[0].title,'Compare options');}
    finally{if(saved===undefined)delete process.env.TMPDIR;else process.env.TMPDIR=saved;sessions.forEach(s=>s.dispose());await new Promise(r=>setTimeout(r,20));fs.rmSync(link,{force:true});fs.rmSync(real,{recursive:true,force:true});}
});
test('single field change targets owned source, creates one WorkspaceEdit and leaves disk untouched',async()=>{
    const {session,d,built}=await open(), from=messages.length;
    await send(session,{type:'edit',generation:built.generation,slide:'s0',node:'s0-card-0',operation:'text',value:'Changed card'});
    await waitFor('compiled',from);assert.equal(applies.length,1);assert.equal(applies[0].edits.length,1);
    assert.match(d.text,/### Changed card/);assert.match(d.text,/Second body/);assert.equal(fs.readFileSync(d.fileName,'utf8'),'OLD DISK SOURCE');
});
test('stale generation after source typing cannot overwrite the changed document',async()=>{
    const {session,d,built}=await open();d.text=d.text.replace('First body','Externally changed body');d.version++;changes.forEach(fn=>fn({document:d}));
    await send(session,{type:'edit',generation:built.generation,slide:'s0',node:'s0-card-0',operation:'text',value:'Wrong edit'});
    assert.equal(applies.length,0);assert.match(d.text,/Externally changed body/);assert.ok(messages.some(m=>m.type==='error'&&/stale/.test(m.message)));
});
test('candidate preview and readonly diff do not mutate source; Apply is one revision-checked edit',async()=>{
    const {session,d,built}=await open(), initial=d.text;
    await send(session,{type:'propose',generation:built.generation,slide:'s0',value:built.manifest.slides[0].source.replace('First body','AI candidate body')});
    const candidate=await waitFor('candidate');assert.equal(d.text,initial);assert.equal(applies.length,0);assert.equal(diffs[0][0],'vscode.diff');
    await send(session,{type:'applyProposal',proposalId:candidate.proposalId});assert.equal(applies.length,1);assert.match(d.text,/AI candidate body/);
});
test('Reject and an expired AI proposal never modify source',async()=>{
    const {session,d,built}=await open(), initial=d.text;
    await send(session,{type:'propose',generation:built.generation,slide:'s0',value:built.manifest.slides[0].source.replace('First body','Candidate')});
    const candidate=await waitFor('candidate');await send(session,{type:'reject'});assert.equal(d.text,initial);
    await send(session,{type:'applyProposal',proposalId:candidate.proposalId});assert.equal(applies.length,0);
});
test('copy request is a disclosed handoff, not a provider call',async()=>{
    const {session,built}=await open();await send(session,{type:'copyRequest',generation:built.generation,slide:'s0',prompt:'Shorten the cards'});
    assert.match(clipboard,/Shorten the cards/);assert.match(clipboard,/SOURCE:/);assert.equal(applies.length,0);assert.ok(messages.some(m=>m.type==='notice'));
});
test('revoking trust blocks writes even with a current map',async()=>{
    const {session,built}=await open();vscode.workspace.isTrusted=false;
    await send(session,{type:'edit',generation:built.generation,slide:'s0',node:'s0-card-0',operation:'text',value:'Forbidden'});assert.equal(applies.length,0);
});
test('failed build retains last good frame and disables writeback',async()=>{
    const {session,d,built}=await open();d.text='---\nremarp: true\n---\n@type: canvas\n## Invalid complex diagram\n:::canvas\n'+Array.from({length:8},(_,i)=>`box n${i} "Node ${i}" at ${i*100},100 size 90,40 color accent`).join('\n')+'\n:::\n';d.version++;
    const from=messages.length;changes.forEach(fn=>fn({document:d}));await waitFor('error',from);
    assert.equal(messages.filter(m=>m.type==='compiled').length,1);assert.equal(session.current.frameHtml,built.frameHtml);assert.equal(session.ready,false);
});
test('closing the panel removes isolated output and late writes are ignored',async()=>{
    const {session,built}=await open(), temporary=session.temporary;assert.ok(fs.existsSync(temporary));session.dispose();assert.ok(!fs.existsSync(temporary));
    await send(session,{type:'edit',generation:built.generation,slide:'s0',node:'s0-card-0',operation:'text',value:'Late'});assert.equal(applies.length,0);
});
test('repeated invalid candidates bound staging and keep the last good renderer alive',async()=>{
    const {session,built}=await open();
    for(let i=0;i<5;i++) {
        await send(session,{type:'propose',generation:built.generation,slide:'s0',value:'@type: canvas\n## Invalid\n:::canvas\n'+Array.from({length:8},(_,n)=>`box n${n} "Node ${n}" at ${n*100},100 size 90,40 color accent`).join('\n')+'\n:::\n'});
    }
    assert.ok(session.stages.length<=3);assert.equal(fs.readdirSync(session.temporary).length,session.stages.length);
    assert.ok(fs.existsSync(session.current.stage));assert.equal(session.ready,true);assert.equal(applies.length,0);
});
test('typing while a proposal is open expires it without overwriting source',async()=>{
    const {session,d,built}=await open();
    await send(session,{type:'propose',generation:built.generation,slide:'s0',value:built.manifest.slides[0].source.replace('First body','Candidate')});
    const candidate=await waitFor('candidate');d.text=d.text.replace('First body','Typed text');d.version++;changes.forEach(fn=>fn({document:d}));
    await send(session,{type:'applyProposal',proposalId:candidate.proposalId});assert.equal(applies.length,0);assert.match(d.text,/Typed text/);
});
test('Canvas drag and resize applies two source spans in exactly one WorkspaceEdit',async()=>{
    const {session,d}=await open();const from=messages.length;
    d.text='---\nremarp: true\n---\n@type: canvas\n## Flow\n:::canvas\nbox a "API" at 80,180 size 120,50 color accent step 1\n:::\n';d.version++;changes.forEach(fn=>fn({document:d}));
    const built=await waitFor('compiled',from);
    await send(session,{type:'edit',generation:built.generation,slide:'s0',node:'s0-canvas-a',operation:'geometry',value:{x:100,y:200,width:160,height:60}});
    assert.equal(applies.length,1);assert.equal(applies[0].edits.length,2);assert.match(d.text,/at 100,200 size 160,60/);
});

async function waitUntil(predicate) {
    for(let n=0;n<200;n++){if(predicate())return;await new Promise(resolve=>setTimeout(resolve,10));}
    throw new Error('Timed out waiting for session state');
}
test('a startup failure lost before shell readiness is replayed with diagnostics',async()=>{
    listening=false;
    const doc=makeDoc(path.join(root,'deck.md'),source);fs.writeFileSync(doc.fileName,'OLD DISK SOURCE');
    const log=[],session=new StudioSession(uri(path.resolve(__dirname,'..')),doc,path.join(root,'missing-compiler.py'),{appendLine:line=>log.push(line)});sessions.push(session);
    await waitUntil(()=>attempts.some(m=>m.type==='error'));
    assert.deepEqual(messages,[]);assert.match(log.join('\n'),/Studio compile failed/);
    listening=true;await send(session,{type:'ready'});
    assert.equal(messages.at(-1).type,'error');assert.equal(messages.at(-1).ready,false);
    assert.equal(messages.at(-1).status,'Studio could not build this source');
    assert.match(messages.at(-1).message,/Studio compile failed/);
    assert.equal(messages.filter(m=>m.type==='compiled').length,0);
});
test('a successful build lost before shell readiness is replayed',async()=>{
    listening=false;
    const doc=makeDoc(path.join(root,'deck.md'),source);fs.writeFileSync(doc.fileName,'OLD DISK SOURCE');
    const session=new StudioSession(uri(path.resolve(__dirname,'..')),doc,compiler);sessions.push(session);
    await waitUntil(()=>attempts.some(m=>m.type==='compiled'));
    assert.deepEqual(messages,[]);listening=true;await send(session,{type:'ready'});
    assert.equal(messages.at(-1).type,'compiled');assert.equal(messages.at(-1).ready,true);
    assert.equal(messages.at(-1).manifest.slides[0].title,'Compare options');
});
test('ready replays building status and entry source is revealable before a successful map',async()=>{
    const doc=makeDoc(path.join(root,'deck.md'),source);fs.writeFileSync(doc.fileName,'OLD DISK SOURCE');
    const session=new StudioSession(uri(path.resolve(__dirname,'..')),doc,compiler);sessions.push(session);
    messages=[];await send(session,{type:'ready'});
    assert.equal(messages.at(-1).type,'status');assert.equal(messages.at(-1).ready,false);
    await send(session,{type:'reveal',file:'/etc/passwd',slide:'not-a-slide'});
    assert.deepEqual(revealed,[doc]);assert.equal(applies.length,0);
});
test('a failed rebuild replays both the last good frame and stale error without enabling edits',async()=>{
    const {session,built}=await open();
    session.ready=false;session.post({type:'status',ready:false,message:'Building — previous preview is stale'});
    session.error(new Error('Broken source'));
    messages=[];await send(session,{type:'ready'});
    assert.deepEqual(messages.map(m=>m.type),['aiSettings','compiled','status','error']);
    assert.ok(messages.filter(m=>m.type!=='aiSettings').every(m=>m.ready===false));assert.equal(messages.find(m=>m.type==='compiled').frameHtml,built.frameHtml);
    assert.match(messages.at(-1).status,/previous preview is stale/);
});
test('candidate preview state survives a repeat ready handshake',async()=>{
    const {session,built}=await open();
    await send(session,{type:'propose',generation:built.generation,slide:'s0',value:built.manifest.slides[0].source.replace('First body','Candidate')});
    const candidate=await waitFor('candidate');messages=[];await send(session,{type:'ready'});
    assert.equal(messages.at(-1).type,'candidate');assert.equal(messages.at(-1).proposalId,candidate.proposalId);assert.equal(messages.at(-1).ready,false);
});
function fakeAI(delay=0,extra='') {
    const file=path.join(root,'fake-ai');
    fs.writeFileSync(file,`#!${process.execPath}\nprocess.stdin.resume();process.stdin.on('end',()=>setTimeout(()=>{${extra}require('fs').writeSync(1,JSON.stringify({type:'result',result:${JSON.stringify(source.slice(source.indexOf('@type:')).replace('First body','Headless candidate'))}}));},${delay}));`,{mode:0o700});
    configValues['claude.executable']=file;return file;
}
test('headless Generate creates a compiled candidate and diff, but only Apply mutates unsaved source',async()=>{
    const {session,d,built}=await open(),initial=d.text;fakeAI();
    await send(session,{type:'generateAI',generation:built.generation,slide:'s0',provider:'claude',prompt:'Shorten the body'});
    const candidate=await waitFor('candidate');assert.equal(d.text,initial);assert.equal(applies.length,0);assert.ok(diffs.length);assert.match(candidate.manifest.slides[0].source,/Headless candidate/);
    await send(session,{type:'applyProposal',proposalId:candidate.proposalId});assert.match(d.text,/Headless candidate/);assert.equal(applies.length,1);assert.equal(fs.readFileSync(d.fileName,'utf8'),'OLD DISK SOURCE');
});
test('Cancel remains responsive while headless generation runs and never offers a late candidate',async()=>{
    const {session,d,built}=await open(),initial=d.text;fakeAI(400);
    await send(session,{type:'generateAI',generation:built.generation,slide:'s0',provider:'claude',prompt:'Edit'});assert.ok(session.ai);
    await send(session,{type:'cancelAI'});assert.equal(session.ai,undefined);await new Promise(r=>setTimeout(r,600));
    assert.equal(d.text,initial);assert.equal(applies.length,0);assert.ok(!messages.some(m=>m.type==='candidate'));assert.ok(messages.some(m=>m.type==='aiStatus'&&/cancelled/.test(m.message)));
});
test('typing cancels headless generation and preserves newly typed source',async()=>{
    const {session,d,built}=await open();fakeAI(400);
    await send(session,{type:'generateAI',generation:built.generation,slide:'s0',provider:'claude',prompt:'Edit'});
    d.text=d.text.replace('First body','User typed body');d.version++;changes.forEach(fn=>fn({document:d}));await new Promise(r=>setTimeout(r,600));
    assert.match(d.text,/User typed body/);assert.equal(applies.length,0);assert.ok(!messages.some(m=>m.type==='candidate'));assert.equal(session.ai,undefined);
});
test('trust revoked during headless execution discards the result',async()=>{
    const {session,d,built}=await open(),initial=d.text;fakeAI(100);
    await send(session,{type:'generateAI',generation:built.generation,slide:'s0',provider:'claude',prompt:'Edit'});vscode.workspace.isTrusted=false;
    const error=await waitFor('error');assert.match(error.message,/trust changed/);assert.equal(d.text,initial);assert.equal(applies.length,0);assert.ok(!session.proposal);
});
test('unsupported providers and invalid prompts never start a CLI; duplicate requests do not overlap',async()=>{
    const {session,built}=await open();fakeAI(300);
    for(const change of [{provider:'gemini'},{prompt:''}])await send(session,{type:'generateAI',generation:built.generation,slide:'s0',provider:'claude',prompt:'Edit',...change});
    assert.equal(session.ai,undefined);
    await send(session,{type:'generateAI',generation:built.generation,slide:'s0',provider:'claude',prompt:'Edit'});const job=session.ai;
    await send(session,{type:'generateAI',generation:built.generation,slide:'s0',provider:'codex',prompt:'Edit'});assert.equal(session.ai,job);await send(session,{type:'cancelAI'});
});
test('closing a Studio panel cancels headless work and ignores late completion',async()=>{
    const {session,d,built}=await open(),initial=d.text;fakeAI(300);
    await send(session,{type:'generateAI',generation:built.generation,slide:'s0',provider:'claude',prompt:'Edit'});session.dispose();await new Promise(r=>setTimeout(r,450));
    assert.equal(session.ai,undefined);assert.equal(d.text,initial);assert.ok(!messages.some(m=>m.type==='candidate'));
});
test('headless settings expose model and effort, default to Claude, and are accessible before rendering',async()=>{
    const {session}=await open();configValues['claude.model']='sonnet';configValues['claude.effort']='high';
    await send(session,{type:'ready'});const settings=messages.find(m=>m.type==='aiSettings');assert.equal(settings.provider,'claude');assert.deepEqual(settings.profiles.claude,{model:'sonnet',effort:'high'});
    await send(session,{type:'aiSettings'});assert.ok(diffs.some(args=>args[0]==='workbench.action.openSettings'&&args[1]==='remarp.ai'));
});

test('headless extra slide separators are rejected by the compiler map, not applied',async()=>{
    const {session,d,built}=await open(),initial=d.text;
    const file=path.join(root,'extra-slide-ai');fs.writeFileSync(file,`#!${process.execPath}\nrequire('fs').writeSync(1,JSON.stringify({type:'result',result:'## First\\nBody\\n---\\n## Unexpected extra\\nBody'}));`,{mode:0o700});configValues['claude.executable']=file;
    await send(session,{type:'generateAI',generation:built.generation,slide:'s0',provider:'claude',prompt:'Edit'});
    const error=await waitFor('error');assert.match(error.message,/structure|another slide/);assert.equal(d.text,initial);assert.equal(applies.length,0);assert.ok(!session.proposal);
});
