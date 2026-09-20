"""Offline human labelling worksheet. Labels are downloaded and explicitly imported."""

import json
from pathlib import Path


def write_review_ui(packet, path: Path):
    data = json.dumps(packet, ensure_ascii=False).replace("<", "\\u003c")
    page = """<!doctype html><meta charset="utf-8"><title>Link Lens human evaluation</title>
<style>body{font:16px system-ui;max-width:1100px;margin:32px auto;background:#f5f7fa;color:#172432}article{background:white;padding:22px;margin:20px 0;border:1px solid #ccd6df;border-radius:8px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}textarea{width:98%;min-height:65px}select,input,button{padding:9px;margin:6px}header{position:sticky;top:0;background:#f5f7fa;padding:10px;border-bottom:1px solid #aaa}</style>
<header><h1 id="title"></h1><p>Human review only. Inspect the evidence; leave uncertain items as unsure. Your choices are saved in this browser. Download the completed JSON and import it through the CLI.</p><label>Your reviewer name <input id="reviewer"></label><button id="download">Download labels</button><span id="progress"></span></header><main id="items"></main>
<script>const original=__DATA__;const key='link-lens-labels-'+original.id;let packet;try{packet=JSON.parse(localStorage.getItem(key))||original}catch{packet=original}
const el=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n};
document.querySelector('#title').textContent=packet.kind==='links'?'Are these records the same business?':'Does this dataset contain identifiable businesses?';
const reviewer=document.querySelector('#reviewer');reviewer.value=packet.items.find(i=>i.reviewer)?.reviewer||'';
function save(){for(const i of packet.items)if(i.verdict)i.reviewer=reviewer.value;localStorage.setItem(key,JSON.stringify(packet));document.querySelector('#progress').textContent=packet.items.filter(i=>i.verdict).length+'/'+packet.items.length+' labelled'}
reviewer.oninput=save;
packet.items.forEach((item,index)=>{const card=el('article');card.append(el('h2',(index+1)+'. '+(item.evidence_to_review.title||item.item_id)));const evidence=item.evidence_to_review;
if(evidence.catalogue_url){const a=el('a','Open catalogue and inspect resource');a.href=evidence.catalogue_url;a.target='_blank';a.rel='noopener';card.append(a)}
const pre=el('pre',JSON.stringify(evidence,null,2));card.append(pre);
const select=el('select');for(const [v,t] of [['','Not reviewed'],['yes','Yes'],['no','No'],['unsure','Unsure']]){const option=el('option',t);option.value=v;select.append(option)}select.value=item.verdict;select.onchange=()=>{item.verdict=select.value;save()};card.append(select);
const reason=el('textarea');reason.placeholder='Evidence you checked and reason (required; at least 8 characters)';reason.value=item.evidence;reason.oninput=()=>{item.evidence=reason.value;save()};card.append(reason);document.querySelector('#items').append(card)});
document.querySelector('#download').onclick=()=>{save();const bad=packet.items.find(i=>i.verdict&&(!i.reviewer.trim()||i.evidence.trim().length<8));if(bad){alert('Every labelled item needs your name and an evidence note of at least 8 characters.');return}const url=URL.createObjectURL(new Blob([JSON.stringify(packet,null,2)],{type:'application/json'}));const a=el('a');a.href=url;a.download=packet.kind+'-review-completed.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};save();</script>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page.replace("__DATA__", data))


def prepare_review_page(packet, path):
    """Add source claims for presentation without changing worksheet selection or labels."""
    from copy import deepcopy
    from . import store

    packet = deepcopy(packet)
    if packet["kind"] == "links":
        batch = store.require("batches", packet["batch_id"])
        result = store.read_json(batch["result_artifact"])
        claims = {}
        for observation in result["observations"]:
            ref = (observation["source_id"], observation["source_record_id"])
            claims.setdefault(ref, []).append(
                {
                    k: observation[k]
                    for k in [
                        "field",
                        "value",
                        "raw_value",
                        "raw_locator",
                        "subject_role",
                    ]
                }
            )
        for item in packet["items"]:
            evidence = item["evidence_to_review"]
            evidence["source_details"] = [
                {
                    "title": store.require("sources", evidence[side][0])["metadata"][
                        "title"
                    ],
                    "claims": claims.get(tuple(evidence[side]), []),
                }
                for side in ["source_a_record", "source_b_record"]
            ]
    write_review_ui(packet, path)
