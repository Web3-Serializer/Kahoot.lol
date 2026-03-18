import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { api } from '../lib/api';
import { Trash2, Plus, Minus, Crown, ArrowLeft } from 'lucide-react';

export default function AdminPage() {
  const {user} = useAuth();
  const [users,setUsers] = useState<any[]>([]);
  const [ci,setCi] = useState<Record<string,string>>({});
  const load = ()=>{api.adminUsers().then(setUsers).catch(()=>{})};
  useEffect(load,[]);
  if(!user?.is_admin) return <div className="min-h-screen flex items-center justify-center text-muted text-sm">admin only</div>;

  return (
    <div className="min-h-screen">
      <nav className="border-b border-border sticky top-0 z-50 bg-bg/80 backdrop-blur-md">
        <div className="max-w-4xl mx-auto px-4 h-11 flex items-center justify-between">
          <span className="text-xs font-bold">Admin</span>
          <a href="/" className="text-[11px] text-muted hover:text-white flex items-center gap-1"><ArrowLeft size={12}/>Back</a>
        </div>
      </nav>
      <div className="max-w-4xl mx-auto px-4 py-6">
        <div className="bg-card border border-border rounded-2xl overflow-hidden">
          <div className="px-4 py-2.5 border-b border-border"><span className="text-[11px] text-muted">{users.length} users</span></div>
          <div className="divide-y divide-border">
            {users.map(u=>(
              <div key={u.id} className="px-4 py-3 flex flex-col sm:flex-row sm:items-center gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{u.username}</span>
                    {u.is_admin&&<span className="text-[8px] bg-accent/15 text-accent px-1.5 py-0.5 rounded-full font-bold">ADMIN</span>}
                    <span className="text-[11px] text-accent font-mono">{u.credits.toFixed(0)} cr</span>
                  </div>
                  <code className="text-[8px] text-zinc-700 font-mono truncate block">{u.token}</code>
                </div>
                <div className="flex items-center gap-1 flex-shrink-0">
                  <input type="number" placeholder="0" value={ci[u.id]||''} onChange={e=>setCi(p=>({...p,[u.id]:e.target.value}))}
                    className="w-14 bg-bg border border-border rounded-lg px-2 py-1 text-[10px] font-mono focus:border-accent/50 transition"/>
                  <Btn icon={<Plus size={11}/>} c="emerald" onClick={async()=>{const a=parseFloat(ci[u.id]||'0');if(!a)return;await api.adminAddCredits(u.id,a);setCi(p=>({...p,[u.id]:''}));load()}}/>
                  <Btn icon={<Minus size={11}/>} c="red" onClick={async()=>{const a=parseFloat(ci[u.id]||'0');if(!a)return;await api.adminAddCredits(u.id,-a);setCi(p=>({...p,[u.id]:''}));load()}}/>
                  {!u.is_admin&&<>
                    <Btn icon={<Crown size={11}/>} c="accent" onClick={async()=>{await api.adminPromote(u.id);load()}}/>
                    <Btn icon={<Trash2 size={11}/>} c="red" onClick={async()=>{if(confirm('Delete?')){await api.adminDelete(u.id);load()}}}/>
                  </>}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
function Btn({icon,c,onClick}:{icon:React.ReactNode;c:string;onClick:()=>void}) {
  const cls:Record<string,string>={emerald:'text-emerald-400 hover:bg-emerald-500/10',red:'text-red-400 hover:bg-red-500/10',accent:'text-accent hover:bg-accent/10'};
  return <button onClick={onClick} className={`p-1.5 rounded-lg transition ${cls[c]}`}>{icon}</button>;
}
