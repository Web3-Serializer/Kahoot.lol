import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { Copy } from 'lucide-react';

export default function LoginPage() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<'login'|'register'>('login');
  const [token, setToken] = useState('');
  const [username, setUsername] = useState('');
  const [err, setErr] = useState('');
  const [newToken, setNewToken] = useState('');
  const [busy, setBusy] = useState(false);

  const doLogin = async () => { if(!token)return; setErr(''); setBusy(true); try{await login(token)}catch(e:any){setErr(e.message)} setBusy(false); };
  const doReg = async () => { if(!username)return; setErr(''); setBusy(true); try{setNewToken(await register(username))}catch(e:any){setErr(e.message)} setBusy(false); };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-sm ani">
        <div className="text-center mb-8">
          <div className="text-3xl mb-2">⚡</div>
          <h1 className="text-xl font-bold">kahoot.lol</h1>
          <p className="text-muted text-xs mt-1">automated game sessions</p>
        </div>
        <div className="bg-card border border-border rounded-2xl p-5">
          <div className="flex bg-bg rounded-lg p-0.5 mb-5">
            {(['login','register'] as const).map(m=>(
              <button key={m} onClick={()=>{setMode(m);setErr('');setNewToken('')}} className={`flex-1 py-1.5 text-xs font-medium rounded-md transition ${mode===m?'bg-card text-white shadow':'text-muted'}`}>
                {m==='login'?'Sign In':'Register'}
              </button>
            ))}
          </div>
          {mode==='login'?(
            <div className="space-y-3">
              <input value={token} onChange={e=>setToken(e.target.value)} onKeyDown={e=>e.key==='Enter'&&doLogin()} placeholder="Access token" className="w-full bg-bg border border-border rounded-xl px-3.5 py-2.5 text-sm font-mono placeholder:text-zinc-700 focus:border-accent/50 transition" />
              <button onClick={doLogin} disabled={busy||!token} className="w-full bg-white text-black font-semibold py-2.5 rounded-xl text-sm hover:bg-zinc-200 disabled:opacity-20 transition">{busy?'...':'Sign In'}</button>
            </div>
          ):(
            <div className="space-y-3">
              <input value={username} onChange={e=>setUsername(e.target.value)} onKeyDown={e=>e.key==='Enter'&&doReg()} placeholder="Username" className="w-full bg-bg border border-border rounded-xl px-3.5 py-2.5 text-sm placeholder:text-zinc-700 focus:border-accent/50 transition" />
              <button onClick={doReg} disabled={busy||!username} className="w-full bg-accent text-white font-semibold py-2.5 rounded-xl text-sm hover:bg-accent/80 disabled:opacity-20 transition">{busy?'...':'Create'}</button>
              {newToken&&(
                <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-xl p-3 ani">
                  <p className="text-[10px] text-emerald-400 font-medium mb-1.5">Save this token:</p>
                  <div className="flex gap-2 items-start">
                    <code className="text-[10px] font-mono text-zinc-400 break-all flex-1 select-all">{newToken}</code>
                    <button onClick={()=>navigator.clipboard.writeText(newToken)} className="p-1 hover:bg-white/5 rounded"><Copy size={11} className="text-zinc-500"/></button>
                  </div>
                </div>
              )}
            </div>
          )}
          {err&&<div className="mt-3 bg-red-500/5 border border-red-500/20 rounded-xl px-3 py-2"><p className="text-[11px] text-red-400">{err}</p></div>}
        </div>
      </div>
    </div>
  );
}
