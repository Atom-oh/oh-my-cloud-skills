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
test('staging skips references outside the project and stages a file-backed archify spec', t => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(),'studio-refs-')); t.after(() => fs.rmSync(root,{recursive:true,force:true}));
    fs.mkdirSync(path.join(root,'specs')); fs.writeFileSync(path.join(root,'specs','diagram.json'),'{"components":[]}');
    const text = ['## Code sample','```html','<script src="/static/app.js"></script>','<a href="/docs">Docs</a>','<img src="../outside.png">','```',
        ':::archify id=flow',' specs/diagram.json',':::',':::archify id=inline','{"components":[]}',':::'].join('\n');
    const out = path.join(root,'snapshot'); stageSnapshot(root,out,new Map([['deck.md',{text}]]));
    assert.ok(fs.existsSync(path.join(out,'specs','diagram.json')));
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

const bodySource = '### Card\r\nOld body\r\n';
const bodyManifest = { version:1, files:{'a.md':'hash'}, slides:[{id:'s0',file:'a.md',source:bodySource,range:{start:0,end:bodySource.length},eol:'\r\n',directives:{},css:null,cssEditable:true,nodes:[{id:'s0-card',kind:'card',label:'Card',text:{start:4,end:8,value:'Card'},body:{start:10,end:18,value:'Old body'}}]}]};
test('body edit keeps the slide EOL and replaces only the mapped span', () => {
    const { patches } = planEdit(bodyManifest,{slide:'s0',node:'s0-card',operation:'body',value:'Line 1\nLine 한글 😀'});
    assert.equal(applyPatches(bodySource,patches),'### Card\r\nLine 1\r\nLine 한글 😀\r\n');
});
const guard = /structural|separator|fence/i;
const body = value => () => planEdit(bodyManifest,{slide:'s0',node:'s0-card',operation:'body',value});
test('body and label edits cannot inject slide separators or block fences', () => {
    for (const value of ['a\n---\nb', 'a\r\n- - -\r\nb', 'a\n:::notes\nb', 'a\n  :::\nb', '---']) assert.throws(body(value), guard, JSON.stringify(value));
    assert.doesNotThrow(body('em-dash — and a--b stay fine'));
});
test('body edits cannot open a code fence: the compiler masks an unclosed fence to end of input and loses later separators', () => {
    // remarp_to_slides.py _fence_open: up to three leading spaces, then three or more backticks or tildes.
    for (const value of ['some text\n```', '```', 'a\n~~~\nb', 'a\r\n   ```js\r\nb', 'a\n````python\nb', 'a\n~~~~\nb']) assert.throws(body(value), guard, JSON.stringify(value));
    // Four leading spaces, shorter runs and inline code are not fences for the compiler either.
    for (const value of ['a\n    ```\nb', 'inline `code` and ``two`` stay fine', 'a ~~ b', 'a\n``\nb']) assert.doesNotThrow(body(value), JSON.stringify(value));
});
test('a ::: anywhere is rejected in labels and bodies: NOTES_PATTERN and the other block patterns are unanchored', () => {
    for (const [m, node] of [[manifest, 's0-heading'], [bodyManifest, 's0-card']]) {
        for (const value of ['Card :::notes', ':::notes', 'Card :::', 'Card ::::notes', 'see `:::notes`']) {
            assert.throws(() => planEdit(m,{slide:'s0',node,operation:'text',value}), guard, `${node} ${JSON.stringify(value)}`);
        }
        assert.doesNotThrow(() => planEdit(m,{slide:'s0',node,operation:'text',value:'Price #1 in C# :: ok'}), node);
    }
    for (const value of ['a :::notes\nb', 'a\n:::\nnotes\nb', 'a\n  :::  notes\nb']) assert.throws(body(value), guard, JSON.stringify(value));
    assert.equal(applyPatches(bodySource, planEdit(bodyManifest,{slide:'s0',node:'s0-card',operation:'text',value:'New'}).patches), '### New\r\nOld body\r\n');
});
test('body edits cannot start a heading line: the Studio reader ends a card body at ^#{1,3}\\s and the cards generator starts a card at ### ', () => {
    for (const value of ['a\n### New card\nb', '## Heading', '# H1\nmore', 'a\r\n### CRLF card\r\nb', 'a\n###\tTabbed\nb', 'a\n ### indented\nb']) assert.throws(body(value), guard, JSON.stringify(value));
    // Bare hash lines are headings too: the body span ends at rstrip(), so retained source whitespace can complete `### `.
    for (const value of ['###', 'a\n#\nb', 'a\r\n##\r\nb', 'text\n  ###', '#']) assert.throws(body(value), guard, JSON.stringify(value));
    // Hashes without a following space, four or more hashes and labels are not card or heading lines.
    for (const value of ['#hashtag at line start', 'C# and F#\nIssue #12', '#### four hashes is not a card', 'a\n####\nb']) assert.doesNotThrow(body(value), JSON.stringify(value));
    assert.doesNotThrow(() => planEdit(manifest,{slide:'s0',node:'s0-heading',operation:'text',value:'# Intro'}));
});
test('a bare hash body value cannot borrow trailing source whitespace: remarp_studio.py ends the body span at rstrip()', () => {
    // bodyManifest's span {10,18} covers 'Old body'; the space after it stays in the file next to the replacement.
    const spaced = '### Card\r\nOld body \r\n';
    const m = { ...bodyManifest, slides:[{ ...bodyManifest.slides[0], source:spaced, range:{start:0,end:spaced.length} }] };
    assert.equal(applyPatches(spaced, planEdit(m,{slide:'s0',node:'s0-card',operation:'body',value:'New'}).patches), '### Card\r\nNew \r\n');
    // '###' plus that retained space would read `### ` to _gen_cards_slide and start an untitled card.
    for (const value of ['###', 'Line 1\n###', 'Line 1\r\n ##']) assert.throws(() => planEdit(m,{slide:'s0',node:'s0-card',operation:'body',value}), guard, JSON.stringify(value));
});
test('Python line-boundary characters are rejected in labels and bodies: the compiler splits lines with str.splitlines()', () => {
    // _mask_code_fences and visible_lines also break on U+000B, U+000C, U+001C-U+001E, U+0085, U+2028 and U+2029;
    // a JavaScript `m` regex sees only LF, CR, U+2028 and U+2029, and the EOL normalisation rewrites only LF/CR/CRLF.
    for (const boundary of ['\v', '\f', '\x1c', '\x1d', '\x1e', '\x85', '\u2028', '\u2029']) {
        for (const value of ['text' + boundary + '```', 'text' + boundary + '---' + boundary + 'more', 'plain' + boundary + 'text']) {
            assert.throws(body(value), guard, JSON.stringify(value));
            for (const [m, node] of [[manifest, 's0-heading'], [bodyManifest, 's0-card']]) {
                assert.throws(() => planEdit(m,{slide:'s0',node,operation:'text',value}), guard, `${node} ${JSON.stringify(value)}`);
            }
        }
    }
    assert.doesNotThrow(body('tabs\tand plain spaces stay fine'));
    assert.doesNotThrow(() => planEdit(manifest,{slide:'s0',node:'s0-heading',operation:'text',value:'tabs\tand plain spaces stay fine'}));
});
test('non-finite, fractional and oversized numbers are rejected before planning', () => {
    const g = { id:'s0-box', kind:'box', label:'Box', geometry:{x:0,y:0,width:10,height:10,canvasWidth:960,canvasHeight:400,centered:false}, position:{start:0,end:1}, size:{start:2,end:3} };
    const m = { ...bodyManifest, slides:[{ ...bodyManifest.slides[0], nodes:[g] }] };
    for (const v of [NaN, Infinity, 1.5, -1, 1e9, '10', null]) {
        assert.throws(() => planEdit(m,{slide:'s0',node:'s0-box',operation:'geometry',value:{x:v,y:0,width:10,height:10}}), /Invalid/);
    }
});
test('malformed intents and unknown owners plan nothing', () => {
    for (const intent of [null, 'x', {slide:'nope',operation:'text'}, {slide:'s0',node:'nope',operation:'text',value:'x'}, {slide:'s0',operation:'rm -rf'}]) {
        assert.throws(() => planEdit(bodyManifest,intent));
    }
});
