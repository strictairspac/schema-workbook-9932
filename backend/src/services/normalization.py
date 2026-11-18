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

def chase_table(attributes,relations,fds):
    """Run the tableau chase once and expose the final equivalence classes."""
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
    return attrs,table,find,steps

def lossless_chase(attributes,relations,fds):
    attrs,table,find,steps=chase_table(attributes,relations,fds)
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


def split_dependencies(dependencies):
    """Expand multi-attribute right sides into single-attribute FDs (deterministic)."""
    fds=set()
    for fd in dependencies:
        lhs=frozenset(fd.get('lhs') or [])
        for rhs in fd.get('rhs') or []:
            if rhs not in lhs:fds.add((lhs,rhs))
    return sorted(fds,key=lambda pair:(len(pair[0]),tuple(sorted(pair[0])),pair[1]))


def semantic_fingerprint(attributes,dependencies):
    """Hash of the full closure map, so any F+-equivalent rewrite yields the same value.

    Only the meaning of the rule set is hashed: attribute order, FD order, duplicate
    FDs, split/merged right sides and removable/redundant dependencies all collapse to
    the same closure map and therefore to the same fingerprint.
    """
    attrs=sorted(set(attributes));fds=split_dependencies(dependencies)
    closures=[]
    for size in range(len(attrs)+1):
        for subset in combinations(attrs,size):
            reachable=closure(subset,fds)&set(attrs)
            closures.append([list(subset),sorted(reachable)])
    payload={'attributes':attrs,'closures':closures}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def semantic_cover(attributes,dependencies):
    """Canonical, F+-invariant cover: for each attribute keep the subset-minimal left sides."""
    attrs=sorted(set(attributes));fds=split_dependencies(dependencies)
    minimal={a:[] for a in attrs}
    for size in range(len(attrs)+1):
        for subset in combinations(attrs,size):
            reachable=closure(subset,fds)&set(attrs)
            for attr in sorted(reachable-set(subset)):
                if not any(other<=set(subset) for other in minimal[attr]):
                    minimal[attr].append(frozenset(subset))
    return [(lhs,rhs) for rhs in attrs for lhs in sorted(minimal[rhs],key=lambda s:(len(s),sorted(s)))]


MAX_FRAGMENTS=12

def _normalize_fragments(fragments):
    out=[]
    for fragment in fragments or []:
        if len(set(fragment or []))!=len(fragment or []):
            raise ValueError('分表内的属性不能重复，请修正后重试')
        cleaned=sorted(set(fragment or []))
        if not cleaned:raise ValueError('分表方案中存在空表，每张分表至少包含一个属性')
        if cleaned not in out:out.append(cleaned)
    if not out:raise ValueError('分表方案至少需要一张分表')
    if len(out)>MAX_FRAGMENTS:raise ValueError(f'分表方案最多{MAX_FRAGMENTS}张分表')
    return sorted(sorted({tuple(f) for f in out}))

def _equivalence_columns(attrs,table,find):
    """Turn chased tableau symbols into concrete values, one fresh value per class."""
    label={};rows={}
    for column,attribute in enumerate(attrs):
        for row in table:
            root=find(row[column])
            if (root,column) in label:continue
            index=len([key for key in label if key[1]==column])+1
            label[(root,column)]=f'{attribute}{index}'
    for row in table:
        rows.setdefault(tuple(label[(find(row[column]),column)] for column in range(len(attrs))),None)
    ordered=sorted(rows)
    return [{'label':index+1,'values':dict(zip(attrs,tuple_values))} for index,tuple_values in enumerate(ordered)]

def _project(rows,fragment):
    attrs=sorted(fragment)
    seen=set()
    for row in rows:seen.add(tuple(row[a] for a in attrs))
    return [dict(zip(attrs,t)) for t in sorted(seen)]

def _natural_join(projections):
    result=[{}]
    for fragment in projections:
        new=[]
        for partial in result:
            for row in fragment:
                if all(attribute not in partial or partial[attribute]==value for attribute,value in row.items()):
                    merged=dict(partial);merged.update(row);new.append(merged)
        result=list({tuple(sorted(row.items())):row for row in new}.values())
    return result

def check_plan_input(attributes,dependencies,fragments):
    """Cheap structural check reused by the API and by the worker."""
    attrs=sorted(set(attributes))
    if not attrs or len(attrs)>MAX_ATTRIBUTES:raise ValueError('关系必须包含1–10个唯一属性；复杂度超限请拆分关系')
    if len(dependencies)>MAX_DEPENDENCIES:raise ValueError('最多64条函数依赖，请先合并重复依赖')
    fds=split_dependencies(dependencies)
    for lhs,rhs in fds:
        if not (set(lhs)|{rhs})<=set(attrs):raise ValueError('函数依赖引用了关系外属性')
    normalized=_normalize_fragments(fragments)
    covered=set().union(*[set(fragment) for fragment in normalized]) if normalized else set()
    if covered!=set(attrs):
        missing=sorted(set(attrs)-covered);extra=sorted(covered-set(attrs))
        detail=[]
        if missing:detail.append('缺少属性 '+', '.join(missing))
        if extra:detail.append('引用关系外属性 '+', '.join(extra))
        raise ValueError('分表方案未覆盖该关系的全部属性：'+'；'.join(detail))
    return attrs,fds,normalized

def verify_decomposition(attributes,dependencies,fragments):
    """Verify a vendor decomposition plan: lossless join, dependency preservation and 3NF.

    Semantics only: dependencies are normalized through their closure, so equivalent
    rewrites of the rule set cannot change the verdict. On a lossy plan the canonical
    counterexample instance (a legal database satisfying every frozen dependency) and
    the phantom tuples produced by joining the fragments' projections are reported.
    """
    attrs,fds,normalized=check_plan_input(attributes,dependencies,fragments)
    fingerprint=semantic_fingerprint(attrs,dependencies)
    cover=semantic_cover(attrs,dependencies)
    relations=[set(fragment) for fragment in normalized]
    chase=lossless_chase(attrs,relations,cover)
    keys,examined=candidate_keys(attrs,cover)
    projected=[]
    for fragment in normalized:projected.extend(projected_dependencies(fragment,fds))
    preserved=all(rhs in closure(lhs,projected) for lhs,rhs in fds)
    normal=[local_3nf(set(fragment),fds) for fragment in normalized]
    result={
        'status':'lossless' if chase['lossless'] else 'lossy',
        'attributes':attrs,
        'fragments':[list(fragment) for fragment in normalized],
        'fragment_coverage':[{'fragment':list(fragment),'candidate_keys':check['candidate_keys'],'is_3nf':check['is_3nf'],'violations':check['violations']} for fragment,check in zip(normalized,normal)],
        'all_3nf':all(check['is_3nf'] for check in normal),
        'dependency_preserved':preserved,
        'candidate_keys':[sorted(key) for key in keys],
        'searched_subsets':examined,
        'minimal_cover':[{'lhs':sorted(lhs),'rhs':rhs} for lhs,rhs in cover],
        'chase':chase,
        'rules_fingerprint':fingerprint,
    }
    if not chase['lossless']:
        table_attrs,table,find,_=chase_table(attrs,relations,cover)
        rows=[counter_row['values'] for counter_row in _equivalence_columns(attrs,table,find)]
        projections=[_project(rows,fragment) for fragment in normalized]
        joined=_natural_join(projections)
        original={tuple(sorted(row.items())) for row in rows}
        extra_rows=[row for row in joined if tuple(sorted(row.items())) not in original]
        result['counterexample']={
            'rows':rows,
            'projections':[{'fragment':list(fragment),'rows':projection} for fragment,projection in zip(normalized,projections)],
            'joined_rows':joined,
            'extra_rows':extra_rows,
            'rows_preserve_dependencies':True,
            'note':'原始行同时满足全部冻结依赖；把各分表投影自然连接后，多出的委托行不可能来自任何原始行。',
        }
    result['checksum']=hashlib.sha256(json.dumps(result,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return result
