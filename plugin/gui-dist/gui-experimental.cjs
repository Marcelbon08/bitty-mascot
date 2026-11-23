"use strict";Object.defineProperties(exports,{__esModule:{value:!0},[Symbol.toStringTag]:{value:"Module"}});const n=require("solid-js/web"),o=require("@opencode/plugin/gui"),m=require("solid-js"),l={idle:{mini:"[o_o]",label:"HOLA MARCELBON",short:"HI",art:` .------. 
| o  o |
|  --  |
 '------' `},thinking:{mini:"[o_?]",label:"PENSANDO",short:"PIENSA",art:` .------. 
| o  o |
|  ~~  |
 '------' `},working:{mini:"[O_o]",label:"TRABAJANDO",short:"TOOL",art:` .------. 
| O  o |
|  ==  |
 '------' `},writing:{mini:"[-_-]>",label:"ESCRIBIENDO",short:"ESCRIBE",art:` .------. 
| -  - |
|  /\\  |
 '------' `},done:{mini:"[^_^]",label:"LISTO",short:"LISTO",art:` .------. 
| ^  ^ |
|  \\/  |
 '------' `},error:{mini:"[x_x]",label:"UPS",short:"ERROR",art:` .------. 
| x  x |
|  oo  |
 '------' `},ask:{mini:"[O_O]",label:"PERMISO?",short:"PERMISO",art:` .------. 
| O  O |
|  ??  |
 '------' `},sleepy:{mini:"[-_-]",label:"DESPIERTA?",short:"ZZZ",art:` .------. 
| -  - |
|  __  |
 '------' `}};function y(e){switch(e){case"session.created":case"permission.replied":case"session.idle":return{mood:"idle",hold:0};case"session.execution.started":case"session.step.started":case"session.compaction.started":return{mood:"thinking",hold:8e3};case"session.step.first-token":case"session.text.started":case"session.text.delta":case"session.reasoning.started":return{mood:"writing",hold:6e3};case"session.tool.called":case"session.tool.input.started":case"session.tool.progress":case"session.shell.started":return{mood:"working",hold:6e3};case"session.tool.success":case"session.text.ended":case"session.step.ended":case"session.execution.succeeded":return{mood:"done",hold:5e3};case"session.tool.failed":case"session.step.failed":case"session.execution.failed":case"session.retry.scheduled":case"session.compaction.failed":return{mood:"error",hold:6e3};case"permission.asked":case"form.created":return{mood:"ask",hold:0};case"session.execution.interrupted":return{mood:"sleepy",hold:4e3};default:return}}const f=["session.created","session.idle","session.execution.started","session.execution.succeeded","session.execution.failed","session.execution.interrupted","session.step.started","session.step.first-token","session.step.ended","session.step.failed","session.text.started","session.text.delta","session.text.ended","session.tool.called","session.tool.input.started","session.tool.progress","session.tool.success","session.tool.failed","session.shell.started","session.compaction.started","session.compaction.failed","session.retry.scheduled","permission.asked","permission.replied","form.created"];var g=n.template("<div style=display:flex;flex-direction:column;gap:12px;padding:16px;align-items:center><pre style=margin:0;font-family:monospace;font-size:14px;line-height:1.1></pre><div style=font-size:12px;opacity:0.8></div><div style=font-size:11px;opacity:0.6>Soy Bitty, tu mascota de OpenCode"),h=n.template("<span>");const[d,c]=m.createSignal("idle");let i;function b(e){const t=y(e);t&&(i&&clearTimeout(i),c(t.mood),t.hold>0&&(i=setTimeout(()=>c("idle"),t.hold)))}function O(){const e=()=>l[d()];return(()=>{var t=g(),a=t.firstChild,s=a.nextSibling;return s.nextSibling,n.insert(a,()=>e().art),n.insert(s,()=>`Bitty · ${e().label}`),t})()}const B=o.Plugin.define({i18n:{en:{title:"Bitty","command.open":"Open Bitty mascot","command.group":"Bitty","panel.title":"Bitty","pill.title":"Bitty, your OpenCode mascot","pill.open":"Open Bitty panel"},es:{title:"Bitty","command.open":"Abrir mascota Bitty","command.group":"Bitty","panel.title":"Bitty","pill.title":"Bitty, tu mascota de OpenCode","pill.open":"Abrir panel de Bitty"}},setup(e){o.createKeyed(()=>e.servers.get("sidecar")?.data,s=>{const p=s,u=f.map(r=>p.on(r,()=>b(r)));return m.onCleanup(()=>{u.forEach(r=>r()),i&&clearTimeout(i)})});const t=()=>`${e.id}:mascota`,a={id:"mascota",get title(){return e.t("panel.title")},closable:"compact",fallback:!0};e.add(o.Panel,{id:"mascota",region:"side",width:"narrow",mobile:{get title(){return e.t("panel.title")},order:45,kind:"menu",icon:"terminal"},list:s=>s.open.includes("mascota")?[a]:[],render:()=>n.createComponent(O,{})}),e.add(o.Command,()=>({id:"mascota",title:e.t("command.open"),keywords:"bitty mascota",group:e.t("command.group"),bind:"mod+alt+b",slash:{name:"bitty"},featured:!0,run:()=>{const s=e.sessions.current();s&&e.layout.toggle(t(),s)}})),e.add(o.MenuItem,()=>{const s=e.sessions.current();return{menu:"session.panel",id:"mascota",title:e.t("panel.title"),icon:"terminal",keybind:`${e.id}.mascota`,opened:!!s&&e.layout.state(t(),s)!=="closed",run:()=>{s&&e.layout.open(t(),s)}}}),e.add(o.ComposerPill,{id:"bitty",show:s=>({label:`Bitty ${l[d()].mini}`,icon:"terminal",title:e.t("pill.title"),rows:[{id:"open",label:e.t("pill.open"),run:()=>e.layout.open(t(),s.session)}]})}),e.add(o.Slot,{at:"window.bottom",render:()=>(()=>{var s=h();return n.insert(s,()=>`Bitty · ${l[d()].label}`),s})()})}});exports.default=B;
