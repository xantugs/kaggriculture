
# Observe public harvests and positions; never read the rival's private state.
_EDGE_TRACK_PARENT=GoldCtl._mk_track
_EDGE_TIMED=('MILK','STRAWBERRY','WOOL','TOMATO')

def _edge_public_tiles(farm):
    out={}
    for y,row in enumerate(farm['tiles']):
        for x,t in enumerate(row):
            if not isinstance(t,dict):continue
            p=t.get('crop') or _GC_ANIM.get(t.get('animal'),{}).get('prod')
            if p in _EDGE_TIMED:
                out[(x,y)]=(p,int(t.get('yield_units',0)),t.get('planted_day',t.get('placed_day')))
    return out

def _edge_track(self,obs):
    before={p:len(self.rival_sales.get(p,())) for p in _EDGE_TIMED}
    _EDGE_TRACK_PARENT(self,obs)
    step=int(obs['step']);farm=obs['farms'][1-self.me]
    positions=[tuple(farm['farmer'])]+[tuple(p) for p in farm['hands']]
    tiles=_edge_public_tiles(farm)
    state=getattr(self,'_edge_flow',None)
    if state is None or step<=state['step']:
        state={'step':step,'tiles':tiles,'positions':positions,'hidden':{},'cargo':{}}
        self._edge_flow=state;return
    if state['step']==step-1:
        if step%24==0:state['cargo']={}
        else:
            for u,oldpos in enumerate(state['positions']):
                if u<len(positions) and oldpos in _GC_ACCESS_SET and positions[u]==oldpos:
                    state['cargo'].pop(u,None)
            for pos,(p,qty,born) in state['tiles'].items():
                if qty<=0:continue
                now=tiles.get(pos)
                remaining=now[1] if now and now[0]==p and now[2]==born else 0
                loss=qty-remaining
                if loss<=0:continue
                tile=farm['tiles'][pos[1]][pos[0]]
                if isinstance(tile,dict) and tile.get('kind')=='WEED':continue
                who=[u for u,oldpos in enumerate(state['positions']) if oldpos==pos and u<len(positions) and positions[u]==pos]
                if len(who)!=1:continue
                u=who[0]
                state['hidden'][p]=state['hidden'].get(p,0.0)+loss
                cargo=state['cargo'].setdefault(u,{})
                cargo[p]=cargo.get(p,0.0)+loss
        for p in _EDGE_TIMED:
            sold=sum(row[2] for row in self.rival_sales.get(p,())[before[p]:])
            state['hidden'][p]=max(0.0,state['hidden'].get(p,0.0)-sold)
            # Floor-price sales leave no inventory trace. Do not accumulate an
            # invisible phantom warehouse there.
            if obs['market']['prices'][p]<=1:state['hidden'][p]=0.0
            q=sum(c.get(p,0.0) for c in state['cargo'].values())
            if q>state['hidden'][p] and q>0:
                for c in state['cargo'].values():c[p]=c.get(p,0.0)*state['hidden'][p]/q
    total=sum(state['hidden'].values())
    if total>100:
        for p in state['hidden']:state['hidden'][p]*=100.0/total
    state.update(step=step,tiles=tiles,positions=positions)

def _edge_phase_forecast(self,obs,p,step,day,hour,fallback):
    state=getattr(self,'_edge_flow',None)
    if p not in _EDGE_TIMED or day<12 or state is None:return fallback
    # Learn delivery hours from the last three days on which this product sold,
    # rather than halving alternate-day milk or inventing off-cycle wool sales.
    sales=self.rival_sales.get(p,())
    dates=sorted({d for d,h,q in sales if d<day},reverse=True)[:3]
    weights={}
    for d,h,q in sales:
        if d in dates:weights[h]=weights.get(h,0.0)+q
    if not weights:return fallback
    forecast={};last=step+4*int(GC_P['mkt_dp_periods'])+4
    def spread(q,earliest,on_day):
        if q<=0:return
        start=max(step,earliest,on_day*24)
        slots=[(on_day*24+h,w) for h,w in weights.items() if on_day*24+h>=start]
        if not slots:
            # Overnight inventories are deposited automatically into the shed.
            slots=[((on_day+1)*24,1.0)]
        total=sum(w for t,w in slots)
        for t,w in slots:
            if t<=last:forecast[t]=forecast.get(t,0.0)+q*w/total
    cargo=state['cargo'];positions=state['positions']
    carried=sum(c.get(p,0.0) for c in cargo.values())
    spread(max(0.0,state['hidden'].get(p,0.0)-carried),step,day)
    for u,c in cargo.items():
        if u<len(positions):
            distance=min(_gc_dist(positions[u],a) for a in _GC_ACCESS)
            spread(c.get(p,0.0),step+distance,day)
    for pos,(product,q,born) in state['tiles'].items():
        if product!=p or q<=0:continue
        distance=min((_gc_dist(pos,u) for u in positions),default=10)
        home=min(_gc_dist(pos,a) for a in _GC_ACCESS)
        spread(q,step+distance+home+1,day)
    # Tomorrow's production phase is visible from planting/placement dates.
    tomorrow=0.0
    for row in obs['farms'][1-self.me]['tiles']:
        for t in row:
            if not isinstance(t,dict):continue
            an=_GC_ANIM.get(t.get('animal'))
            if an and an['prod']==p:
                k=day+1-int(t['placed_day'])-an['fy']
                if k>=0 and k%an['iv']==0:
                    tomorrow+=min(an['held'],1+int(t.get('pending_care_bonus',0)))
            elif t.get('crop')==p:
                _cd=_GC_CROPS.get(p,{}); _fy=int(_cd.get('fy',10)); _iv=max(1,int(_cd.get('iv',2) or 1)); _mx=int(_cd.get('mx',4))
                k=day+1-int(t['planted_day'])-_fy
                if k>=0 and k%_iv==0 and k//_iv+1<=_mx:
                    tomorrow+=2 if int(t.get('fertilized_until_day',-1))>=day else 1
    spread(tomorrow,(day+1)*24,day+1)
    _GC_REPORT['edge_phase_forecasts']=_GC_REPORT.get('edge_phase_forecasts',0)+1
    return lambda s2:forecast.get(s2+1,0.0)

GoldCtl._mk_track=_edge_track

def _edge_dp_sell(self, obs, p, n, step, day, hour, shops, cap_night=None):
    """Units of p to sell this turn (None: not a decision turn, hold). A dynamic programme over the next post-tick
    turns on the exact price curve: exogenous inventory = now - town draws + the rival's forecast sales (its hourly
    pattern over the last days), our stock grows by tonight's carried units at the day boundary."""
    cap = int(GC_P["mkt_dp_cap"]); K = int(GC_P["mkt_dp_periods"])
    if n > cap + 30:
        return n - cap   # far beyond what the programme may hold: sell the excess now, plan the rest next turn
    rd = int(GC_P["mkt_dp_rival_days"])
    byh = {}
    for d, h, q in self.rival_sales.get(p, ()):
        if day - rd <= d < day or (d == day and h < hour):
            byh[h] = byh.get(h, 0.0) + q
    ndays = float(max(1, min(rd, day)))
    rival_h = {h: v / ndays for h, v in byh.items()}
    if GC_P["mkt_dp_fresh"] and not byh:
        _GC_REPORT["gc_dp_fresh"] = _GC_REPORT.get("gc_dp_fresh", 0) + n
        return n
    rv = lambda s2: rival_h.get((s2 + 1) % 24, 0.0)   # forecast rival sales at the market of step s2 + 1
    rv = _edge_phase_forecast(self, obs, p, step, day, hour, rv)
    if GC_P["mkt_dp_farm"]:
        ripe = 0
        for row in obs["farms"][1 - self.me]["tiles"]:
            for t in row:
                if isinstance(t, dict) and (t.get("crop") == p or (t.get("animal") and _GC_ANIM.get(t["animal"], {}).get("prod") == p)):
                    ripe += int(t.get("yield_units", 0) or 0)
        if ripe > 0:
            H = max(1, int(GC_P["mkt_dp_farm_h"])); per = ripe / float(H)
            farm_fc = {s2: per for s2 in range(step, step + H)}
            rv = lambda s2, _f=farm_fc, _h=rival_h: max(_h.get((s2 + 1) % 24, 0.0), _f.get(s2, 0.0))
            _GC_REPORT["gc_dp_farm"] = _GC_REPORT.get("gc_dp_farm", 0) + 1
    ad = globals().get("_AD_STATE")
    if GC_P["mkt_dp_copy_plan"] and not (isinstance(ad, dict) and ad.get("off")) and self._copy_plan_ok(obs, p, step, day):
        K0 = int(GC_P["mkt_dp_periods"])
        plan = self._copy_plan(obs, p, step, min(718, step + 4 * K0 + 4))
        if plan is not None:
            rv = lambda s2, _pl=plan: float(_pl.get(s2 + 1, 0))
            _GC_REPORT["gc_cp_used"] = _GC_REPORT.get("gc_cp_used", 0) + 1
    try:
        self._dp_rv_now[p] = float(rv(step - 1))
    except Exception:
        pass
    if step % 4 != 1 and step > 0:
        if not GC_P["mkt_dp_every"]:
            return None
        nxt = step + ((1 - step) % 4)   # the next post-tick decision
        if sum(rv(s2) for s2 in range(step, nxt)) < float(GC_P["mkt_dp_every_min"]):
            return None
        _GC_REPORT["gc_dp_ahead"] = _GC_REPORT.get("gc_dp_ahead", 0) + 1
    inv0 = int(obs["market"]["inventory"][p])
    dsteps = [step + 4 * k for k in range(K + 1) if step + 4 * k <= 718]
    carried = int(getattr(self, "carried_items", {}).get(p, 0))
    exo = []; stock = []; rq = []; I = float(inv0); cum = n
    for k, t in enumerate(dsteps):
        if k > 0:
            for s2 in range(dsteps[k - 1], t):
                I -= self._town_draw(shops, s2).get(p, 0)
                I += rv(s2)
            if (dsteps[k - 1] // 24) < (t // 24):
                cum += carried
        exo.append(I); stock.append(cum)
        # the rival's forecast sales in the period after this decision (priced at the book our decision leaves)
        rq.append(int(round(sum(rv(s2) for s2 in range(t, min(t + 4, 719))))))
    U = stock[-1]
    # the decision before the day boundary may hold only what the shed takes tonight
    caps = [cap] * len(dsteps)
    if cap_night is not None:
        for k in range(len(dsteps) - 1):
            if (dsteps[k] // 24) < (dsteps[k + 1] // 24):
                caps[k] = max(0, min(cap, int(cap_night)))
    rmax = max(rq) if rq else 0
    imin = int(min(exo)) - 2; imax = int(max(exo)) + U + rmax + 2
    pr = [0.0]
    for i in range(imin, imax + 1):
        pr.append(pr[-1] + _gc_price(p, i))
    w = float(GC_P["mkt_dp_rival_w"])
    if (GC_P["mkt_dp_w_behind"] is not None or GC_P["mkt_dp_w_ahead"] is not None) and day >= int(GC_P["mkt_dp_w_day"]):
        try:
            gap = float(obs["farms"][1 - self.me]["money"]) - float(obs["farms"][self.me]["money"])
        except Exception:
            gap = 0.0
        if GC_P["mkt_dp_w_behind"] is not None and gap > float(GC_P["mkt_dp_w_gap"]):
            w = float(GC_P["mkt_dp_w_behind"]); _GC_REPORT["gc_dp_wb"] = _GC_REPORT.get("gc_dp_wb", 0) + 1
        elif GC_P["mkt_dp_w_ahead"] is not None and -gap > float(GC_P["mkt_dp_w_gap_ahead"]):
            w = float(GC_P["mkt_dp_w_ahead"]); _GC_REPORT["gc_dp_wa"] = _GC_REPORT.get("gc_dp_wa", 0) + 1
    NEG = -1e18; Kd = len(dsteps)
    V = [0.0] * (U + 1); best0 = 0
    for k in range(Kd - 1, -1, -1):
        Vn = [NEG] * (U + 1); base = int(exo[k]) - imin; r = rq[k]
        for c in range(min(stock[k], U) + 1):
            avail = stock[k] - c
            best = NEG; bx = 0
            lo_x = avail if k == Kd - 1 else max(0, avail - caps[k])
            for x in range(lo_x, avail + 1):
                a = base + c
                v = pr[a + x] - pr[a] + V[c + x]
                if w and r:
                    v -= w * (pr[a + x + r] - pr[a + x])
                if v > best:
                    best = v; bx = x
            Vn[c] = best
            if k == 0 and c == 0:
                best0 = bx
        V = Vn
    return int(best0)

GoldCtl._dp_sell=_edge_dp_sell
edge_submission_agent=agent
