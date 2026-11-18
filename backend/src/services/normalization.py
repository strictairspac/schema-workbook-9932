"""Bounded exact closure, candidate-key enumeration, canonical cover, 3NF synthesis and tableau chase."""
from itertools import combinations
import hashlib,json
MAX_ATTRIBUTES=10
MAX_DEPENDENCIES=64

def closure(attrs,fds):
    out=set(attrs)
    while True:
        before=len(out)
        for lhs,rhs in fds:
            if set(lhs)<=out:out.add(rhs)
        if len(out)==before:return out

def candidate_keys(attributes,fds):
    universe=set(attributes)
    if len(universe)>MAX_ATTRIBUTES:raise ValueError('候选键精确搜索最多10个属性（至多1024子集），请拆分关系')
    mandatory=universe-{rhs for _,rhs in fds}
    optional=sorted(universe-mandatory);keys=[];examined=0
    for size in range(len(optional)+1):
        for part in combinations(optional,size):
            candidate=mandatory|set(part)
            if any(k<=candidate for k in keys):continue
            examined+=1
            if universe<=closure(candidate,fds):keys.append(candidate)
    return keys,examined

def canonical_cover(fds):
    cover=list(dict.fromkeys((frozenset(lhs),rhs) for lhs,rhs in fds if rhs not in lhs))
    changed=True
    while changed:
        changed=False
        for i,(lhs,rhs) in enumerate(list(cover)):
            for attr in sorted(lhs):
                reduced=lhs-{attr}
                if rhs in closure(reduced,cover):
                    cover[i]=(reduced,rhs);changed=True;break
            if changed:break
    i=0
    while i<len(cover):
        lhs,rhs=cover[i]
        if rhs in closure(lhs,cover[:i]+cover[i+1:]):cover.pop(i)
        else:i+=1
    return cover

def lossless_chase(attributes,relations,fds):
    attrs=sorted(attributes);table=[[f'a:{a}' if a in relation else f'b:{i}:{a}' for a in attrs] for i,relation in enumerate(relations)];parent={v:v for row in table for v in row};steps=[]
    def find(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    def merge(x,y):
        x=find(x);y=find(y)
        if x==y:return False
        winner=x if x.startswith('a:') else y if y.startswith('a:') else min(x,y)
        loser=y if winner==x else x;parent[loser]=winner
        return True
    changed=True
    while changed:
        changed=False
        for lhs,rhs in fds:
            columns=[attrs.index(a) for a in lhs];outcol=attrs.index(rhs)
            for i in range(len(table)):
                for j in range(i+1,len(table)):
                    if all(find(table[i][c])==find(table[j][c]) for c in columns) and merge(table[i][outcol],table[j][outcol]):
                        changed=True;steps.append({'rows':[i+1,j+1],'dependency':{'lhs':sorted(lhs),'rhs':rhs}})
    witnesses=[i+1 for i,row in enumerate(table) if all(find(row[c])==f'a:{a}' for c,a in enumerate(attrs))]
    return {'lossless':bool(witnesses),'witness_rows':witnesses,'steps':steps,'tableau':[[find(v) for v in row] for row in table]}

def local_3nf(relation,fds):
    attrs=sorted(relation);keys,_=candidate_keys(attrs,[(frozenset(lhs),rhs) for lhs,rhs in projected_dependencies(attrs,fds)])
    prime=set().union(*keys);violations=[]
    for size in range(len(attrs)+1):
        for subset in combinations(attrs,size):
            lhs=set(subset);reachable=closure(lhs,fds)&set(attrs)
            for rhs in reachable-lhs:
                if not set(attrs)<=reachable and rhs not in prime:violations.append({'lhs':sorted(lhs),'rhs':rhs})
    return {'attributes':attrs,'candidate_keys':[sorted(k) for k in keys],'is_3nf':not violations,'violations':violations}

def projected_dependencies(attributes,fds):
    # Exact projection of F+ onto a relation, including dependencies using intermediate outside attributes.
    out=[];attrs=sorted(attributes)
    for size in range(len(attrs)+1):
        for subset in combinations(attrs,size):
            for rhs in (closure(subset,fds)&set(attrs))-set(subset):out.append((frozenset(subset),rhs))
    return out

def analyze(attributes,dependencies):
    attrs=sorted(set(attributes))
    if not attrs or len(attrs)>MAX_ATTRIBUTES:raise ValueError('关系必须包含1–10个唯一属性；复杂度超限请拆分关系')
    if len(dependencies)>MAX_DEPENDENCIES:raise ValueError('最多64条函数依赖，请先合并重复依赖')
    fds=[]
    for fd in dependencies:
        if not set(fd['lhs']+fd['rhs'])<=set(attrs):raise ValueError('函数依赖引用了关系外属性')
        for rhs in fd['rhs']:fds.append((frozenset(fd['lhs']),rhs))
    keys,examined=candidate_keys(attrs,fds);cover=canonical_cover(fds)
    groups={}
    for lhs,rhs in cover:groups.setdefault(lhs,set(lhs)).add(rhs)
    relations=list(groups.values());relations=[r for i,r in enumerate(relations) if not any(r<q or (r==q and j<i) for j,q in enumerate(relations))]
    added_key=None
    if not any(any(key<=relation for key in keys) for relation in relations):
        added_key=sorted(keys[0]);relations.append(set(added_key))
    if not relations:relations=[set(attrs)]
    relations=sorted(relations,key=lambda r:','.join(sorted(r)))
    checks=[local_3nf(r,fds) for r in relations]
    projected=[]
    for relation in relations:projected.extend(projected_dependencies(relation,fds))
    preservation=all(rhs in closure(lhs,projected) for lhs,rhs in fds)
    chase=lossless_chase(attrs,relations,fds)
    result={'attributes':attrs,'candidate_keys':[sorted(k) for k in keys],'searched_subsets':examined,'minimal_cover':[{'lhs':sorted(lhs),'rhs':rhs} for lhs,rhs in cover],'decomposition':[sorted(r) for r in relations],'added_key_relation':added_key,'normal_form_checks':checks,'all_3nf':all(x['is_3nf'] for x in checks),'dependency_preserved':preservation,'chase':chase,'closure_proofs':[{'input':sorted(k),'closure':sorted(closure(k,fds))} for k in keys],'limits':{'attributes':10,'dependencies':64},'method':'精确候选键枚举 + 最小覆盖3NF合成 + tableau chase无损判定'}
    result['checksum']=hashlib.sha256(json.dumps(result,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return result
