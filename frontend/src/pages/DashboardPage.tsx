import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../hooks/useAuth';
import { api } from '../lib/api';
import { Play, Square, LogOut, Shield, ChevronDown, ChevronUp, Zap, Brain, Wifi, WifiOff } from 'lucide-react';

const RX = ['thumbsup','clap','haha','thinking','wow','heart','random'];
const RE: Record<string,string> = {thumbsup:'👍',clap:'👏',haha:'😂',thinking:'🤔',wow:'😮',heart:'❤️',random:'🎲'};
const COLORS: Record<number,string> = {0:'Red',1:'Blue',2:'Yellow',3:'Green'};
const TFA_CLR = ['bg-red-500','bg-blue-500','bg-yellow-500','bg-green-600'];
const THEMES = ['default','hacker','animal','space','meme'];
const MODES = [
  {id:'random',label:'Random',icon:'🎲',desc:'Random answers'},
  {id:'ai',label:'AI',icon:'🧠',desc:'Search + Ollama fallback'},
  {id:'first',label:'First',icon:'☝️',desc:'Always choice 0'},
  {id:'last',label:'Last',icon:'👇',desc:'Always last choice'},
];

export default function DashboardPage() {
  const {user,logout,refresh} = useAuth();
  const [pin,setPin] = useState('');
  const [botCount,setBotCount] = useState(1);
  const [mode,setMode] = useState('random');
  const [spectator,setSpectator] = useState(false);
  const [nameMode,setNameMode] = useState('theme');
  const [nameTheme,setNameTheme] = useState('default');
  const [namePrefix,setNamePrefix] = useState('Bot');
  const [customNames,setCustomNames] = useState('');
  const [delayMin,setDelayMin] = useState(0);
  const [delayMax,setDelayMax] = useState(0);
  const [joinDelay,setJoinDelay] = useState(500);
  const [floodReact,setFloodReact] = useState(false);
  const [floodReaction,setFloodReaction] = useState('random');
  const [floodSpeed,setFloodSpeed] = useState(500);
  const [reactOnWin,setReactOnWin] = useState(false);
  const [winReaction,setWinReaction] = useState('random');
  const [reactOnLose,setReactOnLose] = useState(false);
  const [loseReaction,setLoseReaction] = useState('random');
  const [celebrate,setCelebrate] = useState(false);
  const [celebrateReaction,setCelebrateReaction] = useState('random');
  const [celebrateCount,setCelebrateCount] = useState(10);
  const [autoReconnect,setAutoReconnect] = useState(false);
  const [ollamaModel,setOllamaModel] = useState('llama3.2');
  const [ollamaModels,setOllamaModels] = useState<string[]>([]);
  const [ollamaOk,setOllamaOk] = useState(false);
  const [session,setSession] = useState<string|null>(null);
  const [st,setSt] = useState<any>(null);
  const [err,setErr] = useState('');
  const [busy,setBusy] = useState(false);
  const [showNames,setShowNames] = useState(false);
  const [showReact,setShowReact] = useState(false);
  const [showAdv,setShowAdv] = useState(false);
  const [tfaSeq,setTfaSeq] = useState<number[]>([]);
  const [tab,setTab] = useState<'logs'|'bots'>('logs');
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(()=>{
    api.ollamaStatus(ollamaModel).then(d=>{setOllamaOk(d.available);setOllamaModels(d.models||[])}).catch(()=>{});
  },[ollamaModel]);

  useEffect(()=>{
    if(!session) return;
    const iv = setInterval(async()=>{try{setSt(await api.status(session))}catch{setSt(null);setSession(null)}},1200);
    return ()=>clearInterval(iv);
  },[session]);

  useEffect(()=>{if(logRef.current)logRef.current.scrollTop=logRef.current.scrollHeight},[st?.logs]);

  const start = async()=>{
    setErr('');setBusy(true);
    try{
      const res = await api.start({
        pin,bot_count:botCount,mode,spectator,
        name_mode:nameMode,name_theme:nameTheme,name_prefix:namePrefix,
        custom_names:customNames.split('\n').map(s=>s.trim()).filter(Boolean),
        answer_delay_min:delayMin,answer_delay_max:delayMax,join_delay:joinDelay,
        flood_react:floodReact,flood_reaction:floodReaction,flood_speed:floodSpeed,
        react_on_win:reactOnWin,win_reaction:winReaction,
        react_on_lose:reactOnLose,lose_reaction:loseReaction,
        celebrate,celebrate_reaction:celebrateReaction,celebrate_count:celebrateCount,
        auto_reconnect:autoReconnect,ollama_model:ollamaModel,
      });
      setSession(res.session_id);refresh();
    }catch(e:any){setErr(e.message)}
    setBusy(false);
  };

  const stop = async()=>{if(!session)return;try{await api.stop(session)}catch{}setSession(null);setSt(null)};

  const send2fa = async()=>{
    if(!session||tfaSeq.length!==4)return;
    try{await api.submit2fa(session,tfaSeq);setTfaSeq([])}catch(e:any){setErr(e.message)}
  };

  const isLive = !!session && st?.running;

  return (
    <div className="min-h-screen">
      <nav className="border-b border-border sticky top-0 z-50 bg-bg/80 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-4 h-11 flex items-center justify-between">
          <div className="flex items-center gap-2"><Zap size={14} className="text-accent"/><span className="text-xs font-bold tracking-tight">kahoot.lol</span></div>
          <div className="flex items-center gap-3">
            <span className="text-[11px] font-mono text-accent">{user?.credits?.toFixed(0)} cr</span>
            <span className="text-[11px] text-muted">{user?.username}</span>
            {user?.is_admin&&<a href="/admin" className="text-muted hover:text-white transition"><Shield size={13}/></a>}
            <button onClick={logout} className="text-muted hover:text-white transition"><LogOut size={13}/></button>
          </div>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">

          {/* Config */}
          <div className="lg:col-span-2 space-y-3">
            <Card>
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold">Game</span>
                {isLive&&<Live/>}
              </div>
              <div className="grid grid-cols-2 gap-2 mb-3">
                <div><L>PIN</L><Input v={pin} set={setPin} ph="Game PIN" mono/></div>
                <div><L>Bots</L><Input v={String(botCount)} set={v=>setBotCount(Math.max(1,parseInt(v)||1))} type="number" mono/></div>
              </div>
              <L>Mode</L>
              <div className="grid grid-cols-2 gap-1.5 mb-3">
                {MODES.map(m=>(
                  <button key={m.id} onClick={()=>setMode(m.id)} className={`py-2 px-2 rounded-lg text-[11px] border transition text-left ${mode===m.id?'bg-accent/10 border-accent/30':'bg-bg border-border text-muted hover:border-zinc-600'}`}>
                    <span className="mr-1">{m.icon}</span>{m.label}
                    <span className="block text-[9px] text-muted/60 mt-0.5">{m.desc}</span>
                  </button>
                ))}
              </div>

              {/* Ollama config when AI mode */}
              {mode==='ai'&&(
                <div className="bg-bg border border-border rounded-xl p-3 mb-3 ani">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-1.5">
                      <Brain size={12} className="text-accent"/>
                      <span className="text-[11px] font-medium">Ollama</span>
                    </div>
                    <div className="flex items-center gap-1">
                      {ollamaOk?<Wifi size={10} className="text-emerald-400"/>:<WifiOff size={10} className="text-red-400"/>}
                      <span className={`text-[9px] ${ollamaOk?'text-emerald-400':'text-red-400'}`}>{ollamaOk?'connected':'offline'}</span>
                    </div>
                  </div>
                  <L>Model</L>
                  {ollamaModels.length > 0 ? (
                    <select value={ollamaModel} onChange={e=>setOllamaModel(e.target.value)}
                      className="w-full bg-card border border-border rounded-lg px-3 py-2 text-[11px] font-mono focus:border-accent/40 transition">
                      {ollamaModels.map(m=><option key={m} value={m.split(':')[0]}>{m}</option>)}
                    </select>
                  ):(
                    <Input v={ollamaModel} set={setOllamaModel} ph="llama3.2" mono/>
                  )}
                  <p className="text-[9px] text-muted mt-2">
                    {ollamaOk
                      ? "AI will: 1) search Kahoot API → 2) ask Ollama for smart queries → 3) use Q1 answer from game data"
                      : "Install Ollama + pull a model: ollama pull llama3.2"
                    }
                  </p>
                </div>
              )}

              <Toggle label="Spectator (no answers)" checked={spectator} onChange={setSpectator}/>
            </Card>

            <Card><Section title="Bot Names" open={showNames} toggle={()=>setShowNames(!showNames)}>
              <div className="space-y-2">
                <div className="flex gap-1.5">
                  {(['theme','prefix','custom'] as const).map(m=>(
                    <button key={m} onClick={()=>setNameMode(m)} className={`flex-1 py-1.5 rounded-lg text-[10px] font-medium border transition ${nameMode===m?'bg-accent/10 border-accent/30':'bg-bg border-border text-muted'}`}>
                      {m==='theme'?'Theme':m==='prefix'?'Prefix':'Custom'}
                    </button>
                  ))}
                </div>
                {nameMode==='theme'&&<div className="flex gap-1 flex-wrap">{THEMES.map(t=>(<button key={t} onClick={()=>setNameTheme(t)} className={`px-2 py-1 rounded-lg text-[10px] border transition ${nameTheme===t?'bg-accent/10 border-accent/30':'bg-bg border-border text-muted'}`}>{t}</button>))}</div>}
                {nameMode==='prefix'&&<Input v={namePrefix} set={setNamePrefix} ph="Prefix"/>}
                {nameMode==='custom'&&<textarea value={customNames} onChange={e=>setCustomNames(e.target.value)} placeholder="One per line" rows={3} className="w-full bg-bg border border-border rounded-lg px-3 py-2 text-[11px] font-mono placeholder:text-zinc-700 resize-none focus:border-accent/40 transition"/>}
              </div>
            </Section></Card>

            <Card><Section title="Reactions" open={showReact} toggle={()=>setShowReact(!showReact)}>
              <div className="space-y-2.5">
                <Toggle label="Flood Reactions" checked={floodReact} onChange={setFloodReact}/>
                {floodReact&&<><Pills v={floodReaction} set={setFloodReaction}/><div className="pl-3 border-l border-accent/20"><L>Speed (ms)</L><Input v={String(floodSpeed)} set={v=>setFloodSpeed(Math.max(100,parseInt(v)||500))} type="number" mono/></div></>}
                <Toggle label="React on Win" checked={reactOnWin} onChange={setReactOnWin}/>
                {reactOnWin&&<Pills v={winReaction} set={setWinReaction}/>}
                <Toggle label="React on Lose" checked={reactOnLose} onChange={setReactOnLose}/>
                {reactOnLose&&<Pills v={loseReaction} set={setLoseReaction}/>}
                <Toggle label="Celebrate (Game Over)" checked={celebrate} onChange={setCelebrate}/>
                {celebrate&&<><Pills v={celebrateReaction} set={setCelebrateReaction}/><div className="pl-3 border-l border-accent/20"><L>Spam count</L><Input v={String(celebrateCount)} set={v=>setCelebrateCount(parseInt(v)||10)} type="number" mono/></div></>}
              </div>
            </Section></Card>

            <Card><Section title="Advanced" open={showAdv} toggle={()=>setShowAdv(!showAdv)}>
              <div className="space-y-2.5">
                <div className="grid grid-cols-2 gap-2">
                  <div><L>Delay min (ms)</L><Input v={String(delayMin)} set={v=>setDelayMin(parseInt(v)||0)} type="number" mono/></div>
                  <div><L>Delay max (ms)</L><Input v={String(delayMax)} set={v=>setDelayMax(parseInt(v)||0)} type="number" mono/></div>
                </div>
                <div><L>Join delay (ms)</L><Input v={String(joinDelay)} set={v=>setJoinDelay(parseInt(v)||0)} type="number" mono/></div>
                <Toggle label="Auto-reconnect" checked={autoReconnect} onChange={setAutoReconnect}/>
              </div>
            </Section></Card>

            {err&&<div className="bg-red-500/5 border border-red-500/20 rounded-xl px-3 py-2"><p className="text-[10px] text-red-400">{err}</p></div>}
            {!isLive?(
              <button onClick={start} disabled={busy||!pin} className="w-full bg-white text-black font-semibold py-3 rounded-xl text-sm hover:bg-zinc-200 disabled:opacity-20 transition flex items-center justify-center gap-2">
                <Play size={14}/>{busy?'Starting...':`Launch — ${botCount} cr`}
              </button>
            ):(
              <button onClick={stop} className="w-full bg-red-500/10 border border-red-500/20 text-red-400 font-medium py-3 rounded-xl text-sm hover:bg-red-500/20 transition flex items-center justify-center gap-2">
                <Square size={14}/>Stop All
              </button>
            )}
          </div>

          {/* Live */}
          <div className="lg:col-span-3 space-y-3">
            {st?(
              <>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                  <Stat v={st.connected} l="Online" c="emerald"/>
                  <Stat v={st.correct} l="Correct" c="emerald"/>
                  <Stat v={st.wrong} l="Wrong" c="red"/>
                  <Stat v={st.points} l="Points" c="violet"/>
                  <Stat v={st.questions_seen} l="Questions" c="blue"/>
                </div>

                {/* AI + Ollama status */}
                {st.quiz_found&&<div className="bg-emerald-500/5 border border-emerald-500/20 rounded-xl px-3 py-2 flex items-center gap-2">
                  <span className="text-[11px] text-emerald-400">✓ Quiz: "{st.quiz_title}" — {st.answers_count} answers</span>
                </div>}
                {mode==='ai'&&!st.quiz_found&&st.questions_seen>0&&<div className="bg-amber-500/5 border border-amber-500/20 rounded-xl px-3 py-2">
                  <span className="text-[11px] text-amber-400">⚠ Quiz not found — Q2+ will be random</span>
                </div>}
                {st.ollama&&<div className="bg-accent/5 border border-accent/20 rounded-xl px-3 py-1.5">
                  <span className="text-[10px] text-accent flex items-center gap-1"><Brain size={10}/>Ollama active</span>
                </div>}

                {/* 2FA */}
                {st.needs_2fa&&(
                  <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-4 ani">
                    <p className="text-xs text-amber-400 font-medium mb-3">🔐 2FA — tap colors from host screen:</p>
                    <div className="flex gap-2 mb-3">
                      {[0,1,2,3].map(c=>(
                        <button key={c} onClick={()=>setTfaSeq(p=>[...p.slice(0,3),c])} className={`flex-1 h-12 sm:h-14 rounded-xl ${TFA_CLR[c]} hover:opacity-80 transition font-bold text-white text-xs`}>
                          {COLORS[c]}
                        </button>
                      ))}
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="flex gap-1 flex-1">
                        {[0,1,2,3].map(i=>(
                          <div key={i} className={`w-8 h-8 rounded-lg border-2 flex items-center justify-center text-[10px] font-bold text-white ${i<tfaSeq.length?TFA_CLR[tfaSeq[i]]+' border-transparent':'border-zinc-700 bg-bg'}`}>
                            {i<tfaSeq.length?COLORS[tfaSeq[i]]?.[0]:''}
                          </div>
                        ))}
                      </div>
                      <button onClick={()=>setTfaSeq([])} className="text-[10px] text-muted px-2 py-1 rounded hover:text-white transition">Clear</button>
                      <button onClick={send2fa} disabled={tfaSeq.length!==4} className="bg-amber-500 text-black font-semibold text-[11px] px-4 py-1.5 rounded-lg disabled:opacity-30 hover:bg-amber-400 transition">Submit</button>
                    </div>
                  </div>
                )}

                {/* Tabs */}
                <div className="bg-card border border-border rounded-2xl overflow-hidden">
                  <div className="flex border-b border-border">
                    {(['logs','bots'] as const).map(t=>(
                      <button key={t} onClick={()=>setTab(t)} className={`flex-1 py-2 text-[11px] font-medium transition ${tab===t?'text-white bg-bg':'text-muted hover:text-white'}`}>
                        {t==='logs'?`Logs (${st.logs?.length||0})`:`Bots (${st.bots?.length||0})`}
                      </button>
                    ))}
                  </div>
                  {tab==='logs'?(
                    <div ref={logRef} className="h-[400px] sm:h-[460px] overflow-y-auto p-3 space-y-px">
                      {(st.logs||[]).map((l:string,i:number)=>(
                        <div key={i} className={`text-[10px] font-mono leading-[18px] ${
                          l.includes('] +')?'text-emerald-400':
                          l.includes('] -')||l.includes('] !')?'text-red-400':
                          l.includes('] >')?'text-blue-400':
                          l.includes('] *')?'text-accent':
                          l.includes('] ~')?'text-amber-400':
                          l.includes('] i')?'text-cyan-400':
                          'text-zinc-600'
                        }`}>{l}</div>
                      ))}
                      {(!st.logs||!st.logs.length)&&<div className="text-zinc-700 text-xs text-center pt-20">waiting...</div>}
                    </div>
                  ):(
                    <div className="h-[400px] sm:h-[460px] overflow-y-auto p-3">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {(st.bots||[]).map((b:any,i:number)=>(
                          <div key={i} className={`rounded-xl border p-3 ${b.connected?'border-emerald-500/20 bg-emerald-500/5':'border-border bg-bg'}`}>
                            <div className="flex items-center justify-between mb-1.5">
                              <span className="text-xs font-medium">{b.name}</span>
                              <span className={`text-[9px] px-1.5 py-0.5 rounded-full ${b.connected?'bg-emerald-500/20 text-emerald-400':'bg-zinc-800 text-zinc-500'}`}>{b.connected?'online':'off'}</span>
                            </div>
                            <div className="grid grid-cols-4 gap-1">
                              <Mini l="Score" v={b.score}/><Mini l="Rank" v={b.rank?`#${b.rank}`:'-'}/><Mini l="W/L" v={`${b.correct}/${b.wrong}`}/><Mini l="Streak" v={b.streak}/>
                            </div>
                          </div>
                        ))}
                      </div>
                      {(!st.bots||!st.bots.length)&&<div className="text-zinc-700 text-xs text-center pt-20">no bots</div>}
                    </div>
                  )}
                </div>
              </>
            ):(
              <div className="bg-card border border-border rounded-2xl h-[550px] flex items-center justify-center">
                <div className="text-center"><div className="text-4xl mb-4">🎯</div><p className="text-sm text-zinc-400">Configure and launch</p><p className="text-xs text-zinc-700 mt-1">Live data here</p></div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Card({children}:{children:React.ReactNode}){return<div className="bg-card border border-border rounded-2xl p-4">{children}</div>}
function L({children}:{children:React.ReactNode}){return<label className="text-[10px] text-muted uppercase tracking-wider mb-1 block">{children}</label>}
function Input({v,set,ph,mono,type}:{v:string;set:(v:string)=>void;ph?:string;mono?:boolean;type?:string}){
  return<input type={type||'text'} value={v} onChange={e=>set(e.target.value)} placeholder={ph} className={`w-full bg-bg border border-border rounded-lg px-3 py-2 text-[11px] placeholder:text-zinc-700 focus:border-accent/40 transition ${mono?'font-mono':''}`}/>
}
function Toggle({label,checked,onChange}:{label:string;checked:boolean;onChange:(v:boolean)=>void}){
  return<div className="flex items-center justify-between cursor-pointer" onClick={()=>onChange(!checked)}>
    <span className="text-[11px] text-zinc-400 select-none">{label}</span>
    <div className={`w-7 h-4 rounded-full relative transition ${checked?'bg-accent':'bg-zinc-800'}`}><div className={`w-3 h-3 bg-white rounded-full absolute top-0.5 transition-transform ${checked?'translate-x-3.5':'translate-x-0.5'}`}/></div>
  </div>
}
function Section({title,open,toggle,children}:{title:string;open:boolean;toggle:()=>void;children:React.ReactNode}){
  return<><button onClick={toggle} className="w-full flex items-center justify-between text-xs font-semibold">{title}{open?<ChevronUp size={14} className="text-muted"/>:<ChevronDown size={14} className="text-muted"/>}</button>{open&&<div className="mt-3 ani">{children}</div>}</>
}
function Pills({v,set}:{v:string;set:(v:string)=>void}){
  return<div className="flex gap-1 pl-3 border-l border-accent/20 flex-wrap">{RX.map(r=>(<button key={r} onClick={()=>set(r)} className={`w-6 h-6 rounded-md text-[11px] flex items-center justify-center transition ${v===r?'bg-accent/20 ring-1 ring-accent/40':'bg-bg hover:bg-zinc-800'}`}>{RE[r]}</button>))}</div>
}
function Stat({v,l,c}:{v:number|string;l:string;c:string}){
  const C:Record<string,string>={emerald:'text-emerald-400 bg-emerald-500/5 border-emerald-500/10',red:'text-red-400 bg-red-500/5 border-red-500/10',violet:'text-violet-400 bg-violet-500/5 border-violet-500/10',blue:'text-blue-400 bg-blue-500/5 border-blue-500/10'};
  return<div className={`border rounded-xl px-2 py-2 text-center ${C[c]}`}><div className="text-base font-bold font-mono">{v}</div><div className="text-[9px] opacity-60 uppercase">{l}</div></div>
}
function Mini({l,v}:{l:string;v:string|number}){return<div className="text-center"><div className="text-[11px] font-mono font-bold">{v}</div><div className="text-[8px] text-muted uppercase">{l}</div></div>}
function Live(){return<span className="text-[9px] bg-emerald-500/10 text-emerald-400 px-1.5 py-0.5 rounded-full flex items-center gap-1"><span className="w-1 h-1 bg-emerald-400 rounded-full animate-pulse"/>Live</span>}
