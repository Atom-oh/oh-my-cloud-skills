const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { planEdit, applyPatches } = require('../out/studioModel');
const { sourcePath, stageSnapshot } = require('../out/studioSnapshot');
const source = '## 한글 😀\r\nText\r\n';
const manifest = { version:1, files:{'a.md':'hash'}, slides:[{id:'s0',file:'a.md',source,range:{start:0,end:source.length},eol:'\r\n',directives:{},css:null,cssEditable:true,nodes:[{id:'s0-heading',kind:'heading',label:'Heading',text:{start:3,end:8,value:'한글 😀'},cssTarget:'header'}]}]};
test('text edit preserves CRLF, Unicode and untouched bytes', () => {
    const { patches } = planEdit(manifest,{slide:'s0',node:'s0-heading',operation:'text',value:'New label'});
    assert.equal(applyPatches(source,patches),'## New label\r\nText\r\n');
});
test('style creation and reset are minimal patches', () => {
    const p = planEdit(manifest,{slide:'s0',node:'s0-heading',operation:'style',property:'color',value:'#aabbcc'}).patches;
    assert.equal(p[0].start,source.length);
    assert.match(p[0].text,/:::css\r\n<header>\r\n  color: #aabbcc\r\n<\/header>/);
    assert.deepEqual(planEdit(manifest,{slide:'s0',node:'s0-heading',operation:'style',property:'color',value:null}).patches,[]);
});
test('rejects CSS URL/functions/declarations and arbitrary properties', () => {
    for (const value of ['url(https://bad.invalid)','red;display:none','var(--secret)','</style><script>'])
        assert.throws(() => planEdit(manifest,{slide:'s0',node:'s0-heading',operation:'style',property:'color',value}));
    assert.throws(() => planEdit(manifest,{slide:'s0',node:'s0-heading',operation:'style',property:'position',value:'absolute'}));
});
test('source-only nodes, unknown IDs and invented directives are rejected', () => {
    assert.throws(() => planEdit(manifest,{slide:'s0',node:'missing',operation:'text',value:'x'}));
    assert.throws(() => planEdit(manifest,{slide:'../../other',operation:'source',value:'x'}));
    for (const property of ['script','__proto__','constructor','type'])
        assert.throws(() => planEdit(manifest,{slide:'s0',operation:'directive',property,value:'anything'}));
    assert.throws(() => planEdit(manifest,{slide:'s0',operation:'execute',value:'rm -rf'}));
});
test('directive insert uses original EOL, no general grammar change', () => {
    assert.equal(planEdit(manifest,{slide:'s0',operation:'directive',property:'fit',value:'off'}).patches[0].text,'@fit: off\r\n');
    assert.throws(() => planEdit(manifest,{slide:'s0',operation:'directive',property:'columns',value:'99'}));
});
test('one Canvas gesture plans coordinate and size in one transaction', () => {
    const m = structuredClone(manifest); m.slides[0].nodes.push({id:'box',kind:'box',geometry:{x:10,y:20,width:30,height:40,canvasWidth:960,canvasHeight:400,centered:false},position:{start:0,end:1},size:{start:2,end:3}});
    const intent = {slide:'s0',node:'box',operation:'geometry',value:{x:140,y:180,width:120,height:50}};
    assert.equal(planEdit(m,intent).patches.length,2);
    for (const value of [{x:-1,y:0,width:30,height:40},{x:950,y:380,width:30,height:40},{x:NaN,y:0,width:30,height:40},{x:0,y:0,width:0,height:1}])
        assert.throws(() => planEdit(m,{...intent,value}));
});
test('overlapping and invalid spans fail closed; simultaneous spans retain offsets', () => {
    assert.equal(applyPatches('123456',[{start:1,end:2,text:'A'},{start:4,end:6,text:'B'}]),'1A34B');
    for (const patches of [[{start:1,end:4,text:'a'},{start:2,end:3,text:'b'}],[{start:-1,end:0,text:'x'}],[{start:0,end:999,text:'x'}]]) assert.throws(() => applyPatches('1234',patches));
});
test('issue text cannot terminate the annotation', () => {
    const p = planEdit(manifest,{slide:'s0',operation:'issue',value:'Fix --> <script>'}).patches[0];
    assert.equal((p.text.match(/-->/g)||[]).length,1);
});
test('staging preserves unsaved text and copies only referenced assets', t => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(),'studio-model-')); t.after(() => fs.rmSync(root,{recursive:true,force:true}));
    fs.mkdirSync(path.join(root,'assets')); fs.writeFileSync(path.join(root,'assets','icon.svg'),'<svg/>');
    fs.writeFileSync(path.join(root,'unrelated.secret'),'not an asset');
    const out = path.join(root,'snapshot'); stageSnapshot(root,out,new Map([['a.md',{text:'Unsaved\r\n![Logo](assets/icon.svg)'}]]));
    assert.equal(fs.readFileSync(path.join(out,'a.md'),'utf8'),'Unsaved\r\n![Logo](assets/icon.svg)');
    assert.ok(fs.existsSync(path.join(out,'assets','icon.svg'))); assert.ok(!fs.existsSync(path.join(out,'unrelated.secret')));
});
test('staging also copies runtime-loaded assets: Canvas icon paths and logo front matter', t => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(),'studio-assets-')); t.after(() => fs.rmSync(root,{recursive:true,force:true}));
    for (const file of ['img/service.png','brand/logo.svg','brand/logo-dark.svg','brand/theme-logo.svg']) {
        fs.mkdirSync(path.dirname(path.join(root,file)),{recursive:true}); fs.writeFileSync(path.join(root,file),'x');
    }
    // A short icon name means an AWS service icon, not a project path: a directory called lambda stays out.
    fs.mkdirSync(path.join(root,'lambda')); fs.writeFileSync(path.join(root,'lambda','private.txt'),'not an asset');
    const text = ['---','logoSrc: brand/logo.svg','logoDark: "brand/logo-dark.svg"','theme:','  logo: brand/theme-logo.svg','---',
        ':::canvas','icon a "img/service.png" at 10,10 size 48','icon b "lambda" at 80,10 size 48',':::'].join('\n');
    const out = path.join(root,'snapshot'); stageSnapshot(root,out,new Map([['deck.md',{text}]]));
    for (const file of ['img/service.png','brand/logo.svg','brand/logo-dark.svg','brand/theme-logo.svg']) assert.ok(fs.existsSync(path.join(out,file)),file);
    assert.ok(!fs.existsSync(path.join(out,'lambda')));
});
test('traversal, absolute paths and escaping symlinks are rejected', t => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(),'studio-bound-')); t.after(() => fs.rmSync(root,{recursive:true,force:true}));
    for (const file of ['../other','/tmp/other','nested\\other']) assert.throws(() => sourcePath(root,file));
    fs.symlinkSync(os.tmpdir(),path.join(root,'escape')); assert.throws(() => sourcePath(root,'escape'));
    assert.throws(() => sourcePath(root,'escape/not-existing-studio-file'));
});
test('asset ancestor cycles and in-root symlink components fail closed', t => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(),'studio-cycle-')); t.after(() => fs.rmSync(root,{recursive:true,force:true}));
    fs.mkdirSync(path.join(root,'assets')); fs.writeFileSync(path.join(root,'assets','icon.svg'),'<svg/>');
    fs.symlinkSync(root,path.join(root,'assets','cycle'));
    fs.symlinkSync(path.join(root,'assets'),path.join(root,'alias'));
    for (const ref of ['assets','alias/icon.svg']) {
        assert.throws(() => stageSnapshot(root,path.join(root,'snapshot'),new Map([['a.md',{text:`![Asset](${ref})`}]])),/symlinks/);
    }
});
