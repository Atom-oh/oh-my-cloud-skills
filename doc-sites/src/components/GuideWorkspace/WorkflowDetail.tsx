import React, {useEffect, useRef, useState} from 'react';
import Link from '@docusaurus/Link';
import useBaseUrl from '@docusaurus/useBaseUrl';
import {translate} from '@docusaurus/Translate';
import type {Workflow} from './workflows';
import type {Guide} from './guides';
import Icon from './Icon';
import styles from './styles.module.css';

export default function WorkflowDetail({workflow, guide, host, checked, onCheck, onBack}: {
  workflow: Workflow; guide: Guide; host: 'claude' | 'codex'; checked: boolean;
  onCheck: (value: boolean) => void; onBack: () => void;
}) {
  const [copied, setCopied] = useState('');
  const [setupOpen, setSetupOpen] = useState(false);
  const [previewOpen, setPreviewOpen] = useState(false);
  const preview = useRef<HTMLDialogElement>(null);
  const image = useBaseUrl(workflow.image || '/img/logo.svg');
  const demo = useBaseUrl(workflow.demo || '/');
  const dashboard = ['pr-dash', 'agent-dash'].includes(workflow.plugin);
  const prompt = host === 'codex' && dashboard && guide.codexPrompt ? guide.codexPrompt : workflow.prompt;
  const result = host === 'codex' && dashboard && guide.codexResult ? guide.codexResult : workflow.result;
  const check = host === 'codex' && dashboard && guide.codexCheck ? guide.codexCheck : workflow.check;
  const install = host === 'claude'
    ? `/plugin marketplace add Atom-oh/oh-my-cloud-skills\n/plugin install ${guide.id}@oh-my-cloud-skills`
    : 'codex plugin marketplace add Atom-oh/oh-my-cloud-skills';
  useEffect(() => {setCopied(''); setSetupOpen(false); preview.current?.close(); setPreviewOpen(false);}, [workflow.id, host]);
  async function copy(text: string) {
    try {await navigator.clipboard.writeText(text); setCopied(translate({id: 'studio.copied', message: 'Copied to clipboard'}));}
    catch {setCopied(translate({id: 'studio.copyError', message: 'Select and copy the text manually.'}));}
  }
  function ask() {
    const question = translate({id: 'studio.askWorkflow', message: 'Walk me through this workflow: {title}'}, {title: workflow.title});
    window.dispatchEvent(new CustomEvent('guide-chat', {detail: {plugin: workflow.plugin, question}}));
  }
  return <article className={styles.detail} aria-label={workflow.title}>
    <div className={styles.detailTop}>
      <button className={styles.mobileBack} onClick={onBack}><Icon name="back" size={16}/>{translate({id: 'studio.back', message: 'Workflows'})}</button>
      <span className={styles.breadcrumb}>{guide.name}<span>/</span>{workflow.output}</span>
      <Link to={workflow.guide} className={styles.referenceLink}><Icon name="book" size={16}/>{translate({id: 'studio.reference', message: 'Full reference'})} ↗</Link>
    </div>
    <header className={styles.detailHeading}>
      <div className={styles.largeIcon}><Icon name={workflow.icon} size={27}/></div>
      <div><h2>{workflow.title}</h2><p>{workflow.summary}</p></div>
    </header>
    <div className={styles.metadata}>
      <code>{workflow.skill}</code>
      <span><Icon name="terminal" size={14}/>{host === 'claude' ? 'Claude Code' : 'Codex'}</span>
      <span className={checked ? styles.complete : ''}><Icon name={checked ? 'check' : 'book'} size={14}/>
        {checked ? translate({id: 'studio.verified', message: 'Checked by you'}) : translate({id: 'studio.handsOn', message: 'Hands-on guide'})}</span>
    </div>
    {host === 'codex' && dashboard && <p className={styles.hostNotice}>
      {translate({id: 'studio.hostNotice', message: 'The visual pane is a Claude Code feature. This Codex exercise uses the installed text status procedure.'})}
    </p>}
    <details className={styles.setup} open={setupOpen} onToggle={(e) => setSetupOpen(e.currentTarget.open)}>
      <summary><span className={styles.stepNumber}>1</span><strong>{translate({id: 'studio.setup', message: 'Install & prepare'})}</strong>
        <span>{translate({id: 'studio.setupHint', message: 'First time with this plugin?'})}</span></summary>
      <div className={styles.setupBody}>
        <p>{host === 'claude'
          ? translate({id: 'studio.setupClaude', message: 'Run these commands inside Claude Code, then start a new session.'})
          : translate({id: 'studio.setupCodex', message: 'Run this in your terminal. Open /plugins in Codex, install the selected plugin, then start a new thread.'})}</p>
        <div className={styles.installCode}><pre><code>{install}</code></pre>
          <button onClick={() => copy(install)} aria-label={translate({id: 'studio.copyInstall', message: 'Copy installation commands'})}><Icon name="copy" size={16}/></button></div>
        <Link to={guide.setup}>{translate({id: 'studio.installDetails', message: 'Requirements and troubleshooting'})} ↗</Link>
      </div>
    </details>
    <section className={styles.requestSection} aria-labelledby="workflow-request">
      <div className={styles.sectionHeading}><span className={styles.stepNumber}>2</span>
        <h3 id="workflow-request">{translate({id: 'studio.request', message: 'Try this request'})}</h3>
        <span className={styles.sectionHint}>{translate({id: 'studio.adapt', message: 'Adapt it to your project'})}</span>
      </div>
      <div className={styles.promptCard}>
        <div className={styles.promptToolbar}><span><Icon name="terminal" size={15}/>{host === 'claude' ? 'Claude Code' : 'Codex'}</span>
          <button onClick={() => copy(prompt)}><Icon name="copy" size={15}/>{translate({id: 'studio.copyPrompt', message: 'Copy prompt'})}</button></div>
        <pre><code>{prompt}</code></pre>
      </div>
      <div className={styles.promptFooter}>
        <span role="status">{copied || translate({id: 'studio.promptHint', message: 'Run the request in your own coding assistant.'})}</span>
        <button onClick={ask}><Icon name="spark" size={15}/>{translate({id: 'studio.ask', message: 'Help with this task'})}</button>
      </div>
    </section>
    <section className={styles.resultSection} aria-labelledby="workflow-result">
      <div className={styles.sectionHeading}><span className={styles.stepNumber}>3</span>
        <h3 id="workflow-result">{translate({id: 'studio.result', message: 'Inspect the result'})}</h3></div>
      <div className={styles.resultGrid}>
        <div>
          <p className={styles.resultLabel}>{translate({id: 'studio.expect', message: 'Expected output'})}</p><p>{result}</p>
          <div className={styles.verification}><Icon name="check" size={18}/><p>{check}</p></div>
        </div>
        {workflow.image ? <button className={styles.previewCard} onClick={() => {setPreviewOpen(true); preview.current?.showModal();}}>
          <img src={image} alt={translate({id: 'studio.previewAlt', message: 'Published example for {title}'}, {title: workflow.title})}/>
          <span><Icon name="search" size={15}/>{translate({id: 'studio.preview', message: 'Open published example'})} ↗</span>
        </button> : <div className={styles.outputCard}>
          <div><Icon name={workflow.icon} size={25}/><span>{workflow.output}</span></div>
          <ul>
            <li><Icon name="check" size={14}/>{translate({id: 'studio.outputScope', message: 'Clear scope & assumptions'})}</li>
            <li><Icon name="check" size={14}/>{translate({id: 'studio.outputEvidence', message: 'Evidence you can inspect'})}</li>
            <li><Icon name="check" size={14}/>{translate({id: 'studio.outputAction', message: 'A concrete next action'})}</li>
          </ul>
          <span className={styles.outputHint}>{translate({id: 'studio.outputHint', message: 'Use these as review criteria.'})}</span>
        </div>}
      </div>
      <label className={styles.checkoff}><input type="checkbox" checked={checked} onChange={(e) => onCheck(e.target.checked)}/>
        <span>{translate({id: 'studio.checkoff', message: 'I compared my actual result with this guide.'})}</span></label>
    </section>
    <footer className={styles.detailFooter}>
      <Link to={workflow.guide}><Icon name="book" size={18}/><span>{translate({id: 'studio.deep', message: 'Explore options, constraints and detailed examples'})}</span><Icon name="arrow" size={17}/></Link>
    </footer>
    <dialog ref={preview} className={styles.previewDialog} aria-label={workflow.title} onClose={() => setPreviewOpen(false)}>
      <header><div><strong>{workflow.title}</strong><p>{translate({id: 'studio.exampleNotice', message: 'Archived example of the output format. Follow the current reference for setup and capabilities.'})}</p></div>
        <button onClick={() => preview.current?.close()} aria-label={translate({id: 'studio.closePreview', message: 'Close example'})}><Icon name="close"/></button></header>
      {previewOpen && <img src={image} alt={workflow.title}/>}
      <footer>
        <a href={image} target="_blank" rel="noreferrer">{translate({id: 'studio.fullSize', message: 'Open full size in a new tab'})} ↗</a>
        {workflow.demo && <a href={demo} target="_blank" rel="noreferrer">{translate({id: 'studio.openDemo', message: 'Open the archived interactive example'})} ↗</a>}
      </footer>
    </dialog>
  </article>;
}
