"""Encode each released text independently with a pinned frozen CPU encoder."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
REVISION = '1110a243fdf4706b3f48f1d95db1a4f5529b4d41'

def module(path, name):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

def encode(raw, model_path, cache_path=None):
    import numpy as np
    import torch
    from sentence_transformers import SentenceTransformer
    raw=Path(raw);source=module(raw/'generate.py','source');passages=module(raw/'passages.py','passages')
    texts={}
    for line in (raw/'records.jsonl').read_text(encoding='utf-8').splitlines():
        _,problems,fragments,_=passages.compile_article(json.loads(line),source)
        for item in problems+fragments:
            key=passages.text_key(item['text'])
            if key in texts and texts[key]!=item['text']:raise ValueError('Text checksum collision')
            texts[key]=item['text']
    torch.set_num_threads(4)
    model=SentenceTransformer(str(model_path),device='cpu',local_files_only=True);model.max_seq_length=192
    cached={}
    if cache_path and Path(cache_path).is_file():
        for line in Path(cache_path).read_text().splitlines():
            row=json.loads(line);cached[row['text_sha256']]=row['vector']
    output=[];keys=sorted(texts)
    for offset in range(0,len(keys),512):
        block=keys[offset:offset+512];missing=[k for k in block if k not in cached]
        if missing:
            vectors=model.encode([texts[k] for k in missing],batch_size=32,normalize_embeddings=True,show_progress_bar=False)
            for k,v in zip(missing,vectors):cached[k]=[round(float(x),6) for x in v]
        for key in block:
            vector=cached[key]
            if len(vector)!=384 or not np.isfinite(vector).all():raise ValueError('Invalid encoder output')
            output.append({'text_sha256':key,'vector':vector})
        print('Encoded',min(offset+512,len(keys)),len(keys),flush=True)
    (raw/'embeddings.jsonl').write_text(''.join(json.dumps(r,separators=(',',':'))+'\n' for r in output),encoding='utf-8',newline='\n')
    weights=Path(model_path)/'model.safetensors'
    metadata={'model':MODEL,'revision':REVISION,'model_license':'Apache-2.0','weights_sha256':hashlib.sha256(weights.read_bytes()).hexdigest(),'dimension':384,'maximum_tokens':192,'normalization':'L2 before rounding','decimal_places':6,'text_count':len(texts),'device':'CPU','threads':4,'training_on_release':False,'source_url':'https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2','limits':'Long text is truncated by this fixed encoder; the full text remains supplied. Independent frozen inference only; no corpus-level fitting. Numerical replay may differ slightly across library/hardware versions.'}
    (raw/'encoder_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
    return metadata

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--raw',required=True);parser.add_argument('--model-path',required=True);args=parser.parse_args();print(json.dumps(encode(args.raw,args.model_path)))
