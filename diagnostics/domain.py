"""Reglas puras: BRD v0.6 §§7/7.2 y catálogo aprobado v0.1."""
from importlib.resources import files
from functools import lru_cache
from copy import deepcopy
import json
CHECK_VERSION='1.3'
@lru_cache(maxsize=1)
def catalog():
    return json.loads(files('diagnostics').joinpath('catalog_v0_1.json').read_text(encoding='utf-8'))
def score_answers(options):
    if len(options)!=8:raise ValueError('Se requieren ocho respuestas')
    scores=[]
    for i,v in enumerate(options):
        if i<7:
            if type(v) is not int or v not in (0,1,2):raise ValueError('Respuesta inválida')
            scores.append(v)
        else:
            if v not in ('a','b','c','d','e'):raise ValueError('Financiamiento inválido')
            scores.append({'a':2,'b':2,'c':1,'d':0,'e':2}[v])
    return evaluate(scores)
def evaluate(scores):
    if len(scores)!=8 or any(type(v) is not int or v not in (0,1,2) for v in scores):
        raise ValueError('Se requieren ocho enteros entre cero y dos')
    raw=sum(scores)
    # Redondeo .5 hacia arriba, sin float ni round bancario.
    normalized=(raw*100+8)//16
    strengths=[i+1 for i,v in enumerate(scores) if v==2][:2]
    gaps=sorted([i+1 for i,v in enumerate(scores) if v<2],key=lambda i:(scores[i-1],i))
    eligible=gaps or list(range(1,9))
    data=catalog();index={(a['dimension_id'],a['response_score'],a['order']):a for a in data['actions']}
    selected=[]
    for order in (1,2,3):
        for dim in eligible:
            selected.append(deepcopy(index[dim,scores[dim-1],order]))
            if len(selected)==3:break
        if len(selected)==3:break
    return {'check_version':CHECK_VERSION,'catalog_version':data['catalog_version'],'selection_version':data['selection_policy']['version'],'scores':list(scores),'raw_score':raw,'score':normalized,'level':'Baja visibilidad' if raw<=6 else 'Gestión en desarrollo' if raw<=11 else 'Gestión controlada','strengths':strengths,'gaps':gaps[:2],'actions':selected}
