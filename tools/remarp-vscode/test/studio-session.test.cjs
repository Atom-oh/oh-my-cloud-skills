const { test, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const Module = require('node:module');
let root, docs, changes, received, messages, applies, diffs, clipboard, sessions;
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
    workspace:{isTrusted:true,get textDocuments(){return [...docs.values()];},
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
        onDidReceiveMessage:fn=>{received=fn;return disposable();},postMessage:async m=>{messages.push(m);return true;}}}),
        showTextDocument:async d=>({document:d,selection:undefined,revealRange(){}})}
};
const load=Module._load;Module._load=function(name,...args){return name==='vscode'?vscode:load.call(this,name,...args);};
const {StudioSession}=require('../out/studio');
Module._load=load;
const compiler=path.resolve(__dirname,'../../../plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py');
const source='---\nremarp: true\nratio: "16:9"\n---\n@type: cards\n## Compare options\n### Card one\nFirst body\n### Card two\nSecond body\n';
function makeDoc(file,text){const d={fileName:file,uri:uri(file),text,version:1,isDirty:true,languageId:'remarp',getText(){return this.text;},positionAt:o=>o};docs.set(file,d);return d;}
async function waitFor(type,after=0){for(let n=0;n<200;n++){const m=messages.slice(after).find(m=>m.type===type);if(m)return m;await new Promise(r=>setTimeout(r,10));}throw new Error(`No ${type}: ${JSON.stringify(messages)}`);}
async function open(){const d=makeDoc(path.join(root,'deck.remarp.md'),source);fs.writeFileSync(d.fileName,'OLD DISK SOURCE');const session=new StudioSession(uri(path.resolve(__dirname,'..')),d,compiler);sessions.push(session);return {session,d,built:await waitFor('compiled')};}
async function send(session,message){received(message);await session.messages;}
beforeEach(()=>{root=fs.mkdtempSync(path.join(os.tmpdir(),'studio-session-'));docs=new Map();changes=[];messages=[];applies=[];diffs=[];sessions=[];clipboard='';vscode.workspace.isTrusted=true;});
afterEach(async()=>{sessions.forEach(s=>s.dispose());await new Promise(r=>setTimeout(r,20));fs.rmSync(root,{recursive:true,force:true});});
test('Studio compiles unsaved snapshots without saving or touching published output',async()=>{
    const {d,built}=await open();assert.equal(fs.readFileSync(d.fileName,'utf8'),'OLD DISK SOURCE');
    assert.ok(!fs.existsSync(path.join(root,'slides')));assert.equal(built.manifest.slides[0].title,'Compare options');
    const frame=fs.readFileSync(decodeURI(built.frameUrl.replace('https://resources.example','')),'utf8');
    assert.match(frame,/Compare options/);assert.doesNotMatch(frame,/acquireVsCodeApi/);
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
    assert.equal(messages.filter(m=>m.type==='compiled').length,1);assert.equal(session.current.frameUrl,built.frameUrl);assert.equal(session.ready,false);
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
