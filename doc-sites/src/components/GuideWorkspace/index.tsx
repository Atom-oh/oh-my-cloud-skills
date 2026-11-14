import React, {useEffect, useMemo, useRef, useState} from 'react';
import Link from '@docusaurus/Link';
import {useHistory, useLocation} from '@docusaurus/router';
import {translate} from '@docusaurus/Translate';
import {guides} from './guides';
import {workflows} from './workflows';
import WorkflowDetail from './WorkflowDetail';
import Icon from './Icon';
import styles from './styles.module.css';

const pluginIcons: Record<string, string> = {'aws-content-plugin': 'slides', 'co-agent': 'review', 'project-init': 'project', 'aws-ops-plugin': 'cloud', 'pr-dash': 'branches', 'agent-dash': 'branches'};

function matchesQuery(workflow: typeof workflows[number], query: string) {
  const text = [workflow.title, workflow.summary, workflow.skill, workflow.plugin,
    workflow.output, workflow.prompt, workflow.result, workflow.check].join(' ').toLowerCase();
  return query.toLowerCase().trim().split(/\s+/).filter(Boolean).every((word) => text.includes(word));
}

export default function GuideWorkspace() {
  const location = useLocation();
  const history = useHistory();
  const [selected, setSelected] = useState('all');
  const [activeId, setActiveId] = useState('presentation');
  const [query, setQuery] = useState('');
  const [host, setHost] = useState<'claude' | 'codex'>('claude');
  const [mobileDetail, setMobileDetail] = useState(false);
  const [checks, setChecks] = useState<Record<string, boolean>>({});
  const search = useRef<HTMLInputElement>(null);
  const previousScope = useRef('all');
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const plugin = params.get('plugin');
    const scope = guides.some((g) => g.id === plugin) ? plugin! : 'all';
    const candidates = workflows.filter((w) => scope === 'all' || w.plugin === scope);
    const task = candidates.find((w) => w.id === params.get('task')) || candidates[0];
    setSelected(scope); setActiveId(task.id); setMobileDetail(Boolean(params.get('task')));
    // Restore a historical task even when the current search would hide it.
    if (scope !== previousScope.current || (params.has('task') && !matchesQuery(task, query))) setQuery('');
    previousScope.current = scope;
  }, [location.search]);
  useEffect(() => {
    const focusSearch = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault(); setMobileDetail(false);
        window.requestAnimationFrame(() => search.current?.focus());
      }
    };
    window.addEventListener('keydown', focusSearch);
    return () => window.removeEventListener('keydown', focusSearch);
  }, []);
  const filtered = useMemo(() => workflows.filter((w) =>
    (selected === 'all' || w.plugin === selected) && matchesQuery(w, query)), [selected, query]);
  const active = filtered.find((w) => w.id === activeId) || filtered[0];
  const guide = active ? guides.find((g) => g.id === active.plugin)! : undefined;
  useEffect(() => {
    if (active) window.dispatchEvent(new CustomEvent('guide-context', {detail: active.plugin}));
  }, [active?.plugin]);
  const completed = Object.entries(checks).filter(([key, value]) => key.startsWith(host + ':') && value).length;
  function navigate(plugin: string, task?: string) {
    const params = new URLSearchParams();
    if (plugin !== 'all') params.set('plugin', plugin);
    if (task) params.set('task', task);
    history.push({pathname: location.pathname, search: params.toString() ? `?${params}` : ''});
  }
  function choosePlugin(id: string) {setQuery(''); navigate(id);}
  function chooseTask(id: string) {
    setActiveId(id); setMobileDetail(true); navigate(selected, id);
    if (window.matchMedia('(max-width: 760px)').matches) window.scrollTo(0, 0);
  }
  function ask() {
    window.dispatchEvent(new CustomEvent('guide-chat', {detail: {plugin: active?.plugin, question: ''}}));
  }
  return <main className={styles.workspace}>
    <header className={styles.appHeader}>
      <div><span className={styles.eyebrow}>{translate({id: 'studio.eyebrow', message: 'THE WORKFLOW LIBRARY'})}</span>
        <h1>{translate({id: 'studio.heading', message: 'Choose a task. Put it to work.'})}</h1>
        <p>{translate({id: 'studio.intro', message: '{workflows} practical workflows across {plugins} plugins. Requests, results and verification in one place.'}, {workflows: workflows.length, plugins: guides.length})}</p>
      </div>
      <div className={styles.hostSelector}>
        <span>{translate({id: 'studio.host', message: 'Your assistant'})}</span>
        <div><button aria-pressed={host === 'claude'} onClick={() => setHost('claude')}>Claude Code</button><button aria-pressed={host === 'codex'} onClick={() => setHost('codex')}>Codex</button></div>
      </div>
    </header>
    <div className={styles.shell}>
      <aside className={styles.navigation}>
        <span className={styles.navLabel}>{translate({id: 'studio.browse', message: 'BROWSE WORKFLOWS'})}</span>
        <nav aria-label={translate({id: 'studio.pluginNav', message: 'Filter by plugin'})}>
          <button className={selected === 'all' ? styles.selectedPlugin : ''} onClick={() => choosePlugin('all')} aria-pressed={selected === 'all'}>
            <Icon name="layout"/><span>{translate({id: 'studio.all', message: 'All workflows'})}</span><small>{workflows.length}</small>
          </button>
          {guides.map((g) => <button key={g.id} onClick={() => choosePlugin(g.id)} className={selected === g.id ? styles.selectedPlugin : ''} aria-pressed={selected === g.id}>
            <Icon name={pluginIcons[g.id]}/><span>{g.name}</span><small>{workflows.filter((w) => w.plugin === g.id).length}</small>
          </button>)}
        </nav>
        <div className={styles.navResources}>
          <span className={styles.navLabel}>{translate({id: 'studio.resources', message: 'QUICK REFERENCES'})}</span>
          <Link to="/docs/remarp-guide/keyboard-shortcuts"><Icon name="terminal" size={17}/>{translate({id: 'studio.shortcuts', message: 'Presentation controls'})}</Link>
          <Link to="/docs/aws-content-plugin/presenter-guide"><Icon name="slides" size={17}/>{translate({id: 'studio.presenter', message: 'Presenter handbook'})}</Link>
          <Link to="/docs/intro"><Icon name="book" size={17}/>{translate({id: 'studio.library', message: 'Reference library'})}</Link>
        </div>
        <div className={styles.helperCard}><Icon name="spark" size={22}/>
          <strong>{translate({id: 'studio.helperTitle', message: 'Not sure where to start?'})}</strong>
          <p>{translate({id: 'studio.helperText', message: 'Describe your task. The guide can point you to the relevant workflow.'})}</p>
          <button onClick={ask}>{translate({id: 'studio.helperAction', message: 'Ask the guide'})}<Icon name="arrow" size={16}/></button>
        </div>
        {completed > 0 && <div className={styles.progress}><Icon name="check" size={15}/>{translate({id: 'studio.progress', message: '{count} checked in this session'}, {count: completed})}</div>}
      </aside>
      <div className={`${styles.catalog} ${mobileDetail ? styles.mobileHidden : ''}`}>
        <div className={styles.catalogTop}>
          <label className={styles.search} htmlFor="workflow-search"><Icon name="search" size={18}/>
            <input ref={search} id="workflow-search" value={query} onChange={(e) => {setQuery(e.target.value); setMobileDetail(false);}}
              aria-label={translate({id: 'studio.searchLabel', message: 'Search workflow exercises'})}
              placeholder={translate({id: 'studio.search', message: 'Search tasks, skills, outputs…'})}/>
            {query ? <button onClick={() => {setQuery(''); search.current?.focus();}} aria-label={translate({id: 'studio.clearSearch', message: 'Clear search'})}><Icon name="close" size={15}/></button> : <kbd>⌘ K</kbd>}
          </label>
          <div className={styles.catalogHeading}><strong>{selected === 'all' ? translate({id: 'studio.allTasks', message: 'All tasks'}) : guides.find((g) => g.id === selected)?.name}</strong><span>{filtered.length}</span></div>
        </div>
        <nav className={styles.workflowList} aria-label={translate({id: 'studio.workflowNav', message: 'Workflow exercises'})}>
          {filtered.map((w) => <button key={w.id} onClick={() => chooseTask(w.id)} className={active?.id === w.id ? styles.activeWorkflow : ''} aria-current={active?.id === w.id ? 'page' : undefined}>
            <div className={styles.workflowTitle}><span className={styles.workflowIcon}><Icon name={w.icon} size={18}/></span><strong>{w.title}</strong>{checks[`${host}:${w.id}`] ? <Icon name="check" size={15}/> : <span className={styles.workflowArrow}>›</span>}</div>
            <p>{w.summary}</p><span className={styles.workflowSkill}>{w.skill}</span>
          </button>)}
          {!filtered.length && <div className={styles.empty}><Icon name="search" size={28}/><strong>{translate({id: 'studio.noResults', message: 'No matching workflow'})}</strong><p>{translate({id: 'studio.noResultsHint', message: 'Try a skill name, a shorter phrase, or another plugin.'})}</p><button onClick={() => {setQuery(''); navigate('all');}}>{translate({id: 'studio.reset', message: 'Show all workflows'})}</button></div>}
        </nav>
        <div className={styles.catalogBottom}><Icon name="book" size={15}/>{translate({id: 'studio.catalogNote', message: 'Examples you can adapt, with linked references.'})}</div>
      </div>
      <div className={`${styles.detailWrap} ${!mobileDetail ? styles.mobileDetailHidden : ''}`}>
        {active && guide ? <WorkflowDetail workflow={active} guide={guide} host={host} checked={Boolean(checks[`${host}:${active.id}`])}
          onCheck={(value) => setChecks((previous) => ({...previous, [`${host}:${active.id}`]: value}))} onBack={() => navigate(selected)}/>
          : <div className={styles.detailEmpty}><Icon name="book" size={44}/><h2>{translate({id: 'studio.chooseTask', message: 'Find your next task'})}</h2><p>{translate({id: 'studio.chooseTaskHint', message: 'Search by what you want to make or solve. Each workflow includes a request and verification steps.'})}</p></div>}
      </div>
    </div>
  </main>;
}
