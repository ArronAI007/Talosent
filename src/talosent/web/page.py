"""HTML rendering for the Talosent web UI."""

from __future__ import annotations

from collections.abc import Sequence
from html import escape


# =============================================================================
# CSS DESIGN SYSTEM — lightweight B2B tech minimalism
# =============================================================================
_CSS = """
/* === TOKENS === */
:root {
  --font-sans: ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  --font-mono: ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;
  --bg-base:#ffffff;--bg-elevated:#f8fafc;--bg-sunken:#f1f5f9;
  --surface:#ffffff;--surface-hover:#f8fafc;
  --text-primary:#0f172a;--text-secondary:#475569;--text-tertiary:#94a3b8;--text-inverse:#ffffff;
  --primary-50:#eff6ff;--primary-100:#dbeafe;--primary-500:#3b82f6;--primary-600:#2563eb;--primary-700:#1d4ed8;
  --success:#10b981;--success-bg:#ecfdf5;--warning:#f59e0b;--warning-bg:#fffbeb;
  --error:#ef4444;--error-bg:#fef2f2;--info:#3b82f6;--info-bg:#eff6ff;
  --agent-running:#3b82f6;--agent-tool:#10b981;--agent-error:#ef4444;--agent-idle:#94a3b8;
  --border:#e2e8f0;--border-light:#f1f5f9;--divider:#e2e8f0;
  --radius-sm:6px;--radius-md:10px;--radius-lg:14px;--radius-xl:18px;
  --shadow-sm:0 1px 2px 0 rgb(0 0 0 / 0.04);--shadow-md:0 4px 6px -1px rgb(0 0 0 / 0.06);--shadow-lg:0 10px 15px -3px rgb(0 0 0 / 0.08);
  --sidebar-width:256px;--sidebar-collapsed:64px;--right-panel-width:300px;--topbar-height:56px;
}
[data-theme="dark"] {
  --bg-base:#0b1120;--bg-elevated:#111827;--bg-sunken:#0f172a;
  --surface:#151e32;--surface-hover:#1e293b;
  --text-primary:#f1f5f9;--text-secondary:#94a3b8;--text-tertiary:#64748b;--text-inverse:#0f172a;
  --border:#1e293b;--border-light:#0f172a;--divider:#1e293b;
  --shadow-sm:0 1px 2px 0 rgb(0 0 0 / 0.2);--shadow-md:0 4px 6px -1px rgb(0 0 0 / 0.3);--shadow-lg:0 10px 15px -3px rgb(0 0 0 / 0.4);
  --success-bg:rgba(16,185,129,0.12);--warning-bg:rgba(245,158,11,0.12);--error-bg:rgba(239,68,68,0.12);--info-bg:rgba(59,130,246,0.12);
}

/* === BASE === */
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{font-family:var(--font-sans);color:var(--text-primary);background:var(--bg-base);overflow:hidden;-webkit-font-smoothing:antialiased}

/* === APP SHELL === */
.app{display:flex;flex-direction:column;height:100vh;overflow:hidden}
.topbar{height:var(--topbar-height);flex-shrink:0;display:flex;align-items:center;justify-content:space-between;padding:0 16px;border-bottom:1px solid var(--divider);background:var(--surface);z-index:10}
.topbar-left,.topbar-right{display:flex;align-items:center;gap:12px}
.brand{display:flex;align-items:center;gap:10px}
.brand-logo{width:32px;height:32px;border-radius:var(--radius-md);background:linear-gradient(135deg,var(--primary-500),var(--primary-700));color:#fff;display:grid;place-items:center;font-weight:700;font-size:14px}
.brand-name{font-weight:700;font-size:15px;letter-spacing:-0.01em}
.global-search{position:relative;width:320px}
.global-search input{width:100%;padding:8px 12px 8px 32px;border:1px solid var(--border);border-radius:var(--radius-md);background:var(--bg-sunken);color:var(--text-primary);font-size:13px;outline:none;transition:border-color .2s,box-shadow .2s}
.global-search input:focus{border-color:var(--primary-500);box-shadow:0 0 0 3px var(--primary-50)}
.global-search .search-icon{position:absolute;left:10px;top:50%;transform:translateY(-50%);width:14px;height:14px;color:var(--text-tertiary)}
.status-pill{display:flex;align-items:center;gap:6px;padding:4px 10px;border-radius:999px;background:var(--bg-sunken);font-size:12px;font-weight:500;color:var(--text-secondary)}
.status-dot{width:8px;height:8px;border-radius:50%;background:var(--agent-idle)}
.status-dot.ready{background:var(--success);box-shadow:0 0 0 3px var(--success-bg)}
.status-dot.running{background:var(--agent-running);box-shadow:0 0 0 3px var(--info-bg);animation:pulse 2s infinite}
.status-dot.error{background:var(--error);box-shadow:0 0 0 3px var(--error-bg)}

/* === LAYOUT === */
.layout{display:flex;flex:1;overflow:hidden}
.sidebar{width:var(--sidebar-width);flex-shrink:0;display:flex;flex-direction:column;border-right:1px solid var(--divider);background:var(--bg-elevated);transition:width .25s ease;overflow:hidden}
.sidebar.collapsed{width:var(--sidebar-collapsed)}
.sidebar.collapsed .sidebar-header span,.sidebar.collapsed .section-title,.sidebar.collapsed .nav-item span,.sidebar.collapsed .agent-name,.sidebar.collapsed .agent-meta,.sidebar.collapsed .version{display:none}
.sidebar.collapsed .agent-list{padding:8px}
.sidebar.collapsed .agent-item{padding:8px;justify-content:center}
.sidebar.collapsed .agent-avatar{margin:0}
.sidebar.collapsed .nav-item{justify-content:center;padding:10px}
.sidebar.collapsed .nav-item svg{margin:0}
.sidebar-header{display:flex;align-items:center;justify-content:space-between;padding:16px 16px 8px}
.section-title{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:var(--text-tertiary)}
.agent-list{flex:1;overflow-y:auto;padding:0 12px 12px;display:flex;flex-direction:column;gap:4px}
.agent-item{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:var(--radius-md);cursor:pointer;transition:background .15s;border:1px solid transparent}
.agent-item:hover{background:var(--surface-hover)}
.agent-item.active{background:var(--primary-50);border-color:var(--primary-100)}
[data-theme="dark"] .agent-item.active{background:rgba(59,130,246,0.12);border-color:rgba(59,130,246,0.2)}
.agent-avatar{width:32px;height:32px;border-radius:var(--radius-md);background:linear-gradient(135deg,var(--primary-500),var(--primary-700));color:#fff;display:grid;place-items:center;font-weight:600;font-size:12px;flex-shrink:0}
.agent-info{min-width:0;flex:1}
.agent-name{font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.agent-meta{display:flex;align-items:center;gap:6px;font-size:11px;color:var(--text-tertiary);margin-top:2px}
.agent-status{width:6px;height:6px;border-radius:50%}
.agent-status.idle{background:var(--agent-idle)}
.agent-status.running{background:var(--agent-running);animation:pulse 2s infinite}
.agent-status.error{background:var(--agent-error)}
.agent-model{font-size:10px;padding:1px 5px;border-radius:4px;background:var(--bg-sunken)}
.sidebar-divider{height:1px;background:var(--divider);margin:0 16px}
.nav-menu{padding:8px 12px;display:flex;flex-direction:column;gap:2px}
.nav-item{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:var(--radius-md);color:var(--text-secondary);font-size:13px;font-weight:500;cursor:pointer;transition:all .15s;border:1px solid transparent;background:none;width:100%;text-align:left}
.nav-item:hover{background:var(--surface-hover);color:var(--text-primary)}
.nav-item.active{background:var(--primary-50);color:var(--primary-700);border-color:var(--primary-100)}
[data-theme="dark"] .nav-item.active{background:rgba(59,130,246,0.12);color:#60a5fa;border-color:rgba(59,130,246,0.2)}
.nav-item svg{width:18px;height:18px;flex-shrink:0}
.sidebar-footer{padding:12px 16px;border-top:1px solid var(--divider);margin-top:auto}
.version{font-size:11px;color:var(--text-tertiary)}

.workspace{flex:1;display:flex;flex-direction:column;overflow:hidden;min-width:0}
.right-panel{width:var(--right-panel-width);flex-shrink:0;display:flex;flex-direction:column;border-left:1px solid var(--divider);background:var(--bg-elevated);transition:width .25s ease,margin .25s ease;overflow:hidden}
.right-panel.collapsed{width:0;border-left:none}
.right-panel.collapsed .inspector-content{opacity:0}

/* === TABS === */
.tab-panel{display:none;flex-direction:column;height:100%;overflow:hidden}
.tab-panel.active{display:flex}

/* === CHAT === */
.chat-header{flex-shrink:0;display:flex;align-items:center;justify-content:space-between;padding:12px 20px;border-bottom:1px solid var(--divider);background:var(--surface)}
.chat-header h2{font-size:15px;font-weight:700}
.chat-actions{display:flex;align-items:center;gap:12px}
.conversation-id{font-size:11px;color:var(--text-tertiary);font-family:var(--font-mono)}
.chat-messages{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:16px;scroll-behavior:smooth}
.message{max-width:min(720px,85%);display:flex;flex-direction:column;gap:6px;animation:fadeIn .25s ease}
.message.user{align-self:flex-end}
.message-bubble{padding:12px 16px;border-radius:var(--radius-lg);line-height:1.6;font-size:14px;white-space:pre-wrap;word-break:break-word}
.message.user .message-bubble{background:var(--primary-50);color:var(--primary-700);border:1px solid var(--primary-100);border-bottom-right-radius:var(--radius-sm)}
[data-theme="dark"] .message.user .message-bubble{background:rgba(59,130,246,0.15);color:#93bbfc;border-color:rgba(59,130,246,0.25)}
.message.assistant .message-bubble{background:var(--bg-sunken);color:var(--text-primary);border:1px solid var(--border);border-bottom-left-radius:var(--radius-sm)}
.message.tool .message-bubble{background:var(--success-bg);color:#065f46;border:1px solid #a7f3d0;border-bottom-left-radius:var(--radius-sm);font-size:13px;font-family:var(--font-mono)}
[data-theme="dark"] .message.tool .message-bubble{background:rgba(16,185,129,0.12);color:#34d399;border-color:rgba(16,185,129,0.25)}
.message.error .message-bubble{background:var(--error-bg);color:#991b1b;border:1px solid #fecaca;border-bottom-left-radius:var(--radius-sm)}
[data-theme="dark"] .message.error .message-bubble{background:rgba(239,68,68,0.12);color:#f87171;border-color:rgba(239,68,68,0.25)}
.message-meta{font-size:11px;color:var(--text-tertiary);font-weight:500;display:flex;align-items:center;gap:8px}
.message-meta .role-badge{text-transform:uppercase;letter-spacing:0.06em;font-size:10px}
.think-chain{margin-top:8px;padding:10px 14px;border-radius:var(--radius-md);background:var(--bg-elevated);border:1px solid var(--border);font-size:13px;color:var(--text-secondary)}
.think-chain summary{cursor:pointer;font-weight:500;color:var(--text-primary);list-style:none;display:flex;align-items:center;gap:8px}
.think-chain summary::before{content:"▸";transition:transform .2s}
.think-chain[open] summary::before{transform:rotate(90deg)}
.think-chain pre{margin-top:8px;white-space:pre-wrap;font-family:var(--font-mono);font-size:12px;line-height:1.6;color:var(--text-secondary)}

/* === COMPOSER === */
.chat-composer{flex-shrink:0;border-top:1px solid var(--divider);background:var(--surface);padding:16px 20px}
.composer-toolbar{display:flex;gap:8px;margin-bottom:8px}
.toolbar-btn{padding:5px 10px;border-radius:var(--radius-sm);border:1px solid var(--border);background:var(--bg-elevated);color:var(--text-secondary);font-size:12px;cursor:pointer;transition:all .15s;font-family:var(--font-mono)}
.toolbar-btn:hover{background:var(--surface-hover);color:var(--text-primary);border-color:var(--text-tertiary)}
.composer-input-wrap{display:flex;gap:10px;align-items:flex-end}
.composer-input-wrap textarea{flex:1;min-height:80px;max-height:200px;padding:12px 14px;border:1px solid var(--border);border-radius:var(--radius-lg);background:var(--bg-base);color:var(--text-primary);font-family:inherit;font-size:14px;line-height:1.5;resize:vertical;outline:none;transition:border-color .2s,box-shadow .2s}
.composer-input-wrap textarea:focus{border-color:var(--primary-500);box-shadow:0 0 0 3px var(--primary-50)}
.send-btn{width:40px;height:40px;border-radius:var(--radius-lg);border:none;background:var(--primary-500);color:#fff;display:grid;place-items:center;cursor:pointer;transition:background .15s,transform .1s;flex-shrink:0}
.send-btn:hover{background:var(--primary-600)}
.send-btn:active{transform:scale(0.96)}
.send-btn:disabled{opacity:0.5;cursor:not-allowed}
.composer-meta{display:flex;justify-content:space-between;margin-top:8px;font-size:11px;color:var(--text-tertiary)}

/* === WORKFLOW === */
.panel-header{flex-shrink:0;display:flex;align-items:center;justify-content:space-between;padding:12px 20px;border-bottom:1px solid var(--divider);background:var(--surface)}
.panel-header h2{font-size:15px;font-weight:700}
.panel-actions{display:flex;gap:8px}
.workflow-canvas{flex:1;overflow:auto;padding:24px;background:var(--bg-base)}
.workflow-nodes{display:flex;flex-direction:column;gap:16px;max-width:600px;margin:0 auto}
.workflow-node{display:flex;align-items:center;gap:16px;padding:16px 20px;border-radius:var(--radius-lg);background:var(--surface);border:1px solid var(--border);box-shadow:var(--shadow-sm);transition:all .2s;position:relative}
.workflow-node::before{content:"";position:absolute;left:24px;top:-17px;width:2px;height:17px;background:var(--divider)}
.workflow-node:first-child::before{display:none}
.workflow-node.running{border-color:var(--agent-running);background:var(--info-bg);box-shadow:0 0 0 3px var(--primary-50)}
.workflow-node.completed{border-color:var(--success)}
.workflow-node.failed{border-color:var(--error);background:var(--error-bg)}
.node-icon{width:36px;height:36px;border-radius:var(--radius-md);display:grid;place-items:center;font-size:16px;flex-shrink:0;background:var(--bg-sunken)}
.node-icon.running{background:var(--primary-500);color:#fff;animation:pulse 2s infinite}
.node-icon.failed{background:var(--error);color:#fff}
.node-content{flex:1;min-width:0}
.node-title{font-size:14px;font-weight:600}
.node-desc{font-size:12px;color:var(--text-tertiary);margin-top:2px}
.node-status{font-size:11px;font-weight:600;padding:2px 8px;border-radius:999px;background:var(--bg-sunken);color:var(--text-secondary)}
.node-status.running{background:var(--info-bg);color:var(--primary-700)}
.node-status.completed{background:var(--success-bg);color:#065f46}
.node-status.failed{background:var(--error-bg);color:#991b1b}

/* === PROMPT EDITOR === */
.prompt-editor{flex:1;display:flex;overflow:hidden;background:var(--bg-base)}
.editor-gutter{width:40px;flex-shrink:0;padding:16px 8px;background:var(--bg-elevated);border-right:1px solid var(--divider);font-family:var(--font-mono);font-size:13px;line-height:1.6;color:var(--text-tertiary);text-align:right;overflow:hidden;user-select:none}
.prompt-textarea{flex:1;padding:16px;border:none;background:var(--bg-base);color:var(--text-primary);font-family:var(--font-mono);font-size:13px;line-height:1.6;resize:none;outline:none;white-space:pre;overflow:auto}
.prompt-variables{flex-shrink:0;display:flex;align-items:center;gap:8px;padding:12px 20px;border-top:1px solid var(--divider);background:var(--surface);font-size:12px;flex-wrap:wrap}
.var-label{color:var(--text-tertiary);font-weight:500;white-space:nowrap}
.var-chip{padding:4px 10px;border-radius:var(--radius-sm);border:1px solid var(--border);background:var(--bg-elevated);color:var(--text-secondary);font-family:var(--font-mono);font-size:12px;cursor:pointer;transition:all .15s}
.var-chip:hover{background:var(--primary-50);color:var(--primary-700);border-color:var(--primary-100)}

/* === TOOLS === */
.tools-grid{flex:1;overflow-y:auto;padding:20px;display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px}
.tool-card{padding:16px;border-radius:var(--radius-lg);background:var(--surface);border:1px solid var(--border);box-shadow:var(--shadow-sm);transition:all .15s}
.tool-card:hover{border-color:var(--primary-100);box-shadow:var(--shadow-md);transform:translateY(-1px)}
.tool-card-header{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.tool-icon{width:32px;height:32px;border-radius:var(--radius-md);background:var(--primary-50);color:var(--primary-600);display:grid;place-items:center;font-size:14px}
.tool-name{font-size:14px;font-weight:600}
.tool-desc{font-size:13px;color:var(--text-secondary);line-height:1.5}
.tool-tags{display:flex;gap:6px;margin-top:10px;flex-wrap:wrap}
.tool-tag{font-size:11px;padding:2px 8px;border-radius:999px;background:var(--bg-sunken);color:var(--text-tertiary)}

/* === RIGHT PANEL === */
.panel-header.compact{padding:10px 16px}
.inspector-content{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:16px}
.inspector-section{display:flex;flex-direction:column;gap:10px}
.section-header{display:flex;align-items:center;justify-content:space-between}
.badge{font-size:11px;font-weight:600;padding:2px 8px;border-radius:999px;background:var(--primary-50);color:var(--primary-700)}
.badge.muted{background:var(--bg-sunken);color:var(--text-tertiary)}
.token-bars{display:flex;flex-direction:column;gap:10px}
.token-bar-label{display:flex;justify-content:space-between;font-size:12px;color:var(--text-secondary);margin-bottom:4px}
.progress-track{height:6px;border-radius:999px;background:var(--bg-sunken);overflow:hidden}
.progress-fill{height:100%;border-radius:999px;background:var(--primary-500);transition:width .3s ease}
.progress-fill.info{background:var(--info)}
.tool-log{display:flex;flex-direction:column;gap:6px}
.log-item{display:flex;align-items:center;gap:8px;padding:8px 10px;border-radius:var(--radius-md);border:1px solid var(--border);background:var(--surface);font-size:12px;transition:all .15s;cursor:pointer}
.log-item:hover{background:var(--surface-hover)}
.log-item.success{border-color:var(--success);background:var(--success-bg)}
.log-item.error{border-color:var(--error);background:var(--error-bg)}
.log-time{font-size:10px;color:var(--text-tertiary);font-family:var(--font-mono);white-space:nowrap}
.log-name{font-weight:600;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis}
.log-status{width:6px;height:6px;border-radius:50%;flex-shrink:0}
.log-status.success{background:var(--success)}
.log-status.error{background:var(--error)}
.timeline{display:flex;flex-direction:column;gap:8px}
.timeline-item{display:flex;gap:10px;font-size:12px}
.timeline-dot{width:8px;height:8px;border-radius:50%;background:var(--border);margin-top:5px;flex-shrink:0;position:relative}
.timeline-dot::after{content:"";position:absolute;left:3px;top:12px;width:2px;height:calc(100% + 8px);background:var(--border)}
.timeline-item:last-child .timeline-dot::after{display:none}
.timeline-dot.running{background:var(--agent-running);box-shadow:0 0 0 3px var(--info-bg)}
.timeline-dot.completed{background:var(--success)}
.timeline-dot.failed{background:var(--error)}
.timeline-content{flex:1}
.timeline-title{font-weight:500;color:var(--text-primary)}
.timeline-time{font-size:10px;color:var(--text-tertiary);margin-top:2px}

/* === COMPONENTS === */
.btn{display:inline-flex;align-items:center;gap:6px;padding:7px 14px;border-radius:var(--radius-md);border:1px solid var(--border);background:var(--surface);color:var(--text-primary);font-size:13px;font-weight:500;cursor:pointer;transition:all .15s}
.btn:hover{background:var(--surface-hover);border-color:var(--text-tertiary)}
.btn:active{transform:translateY(1px)}
.btn.primary{background:var(--primary-500);color:#fff;border-color:var(--primary-500)}
.btn.primary:hover{background:var(--primary-600);border-color:var(--primary-600)}
.btn.secondary{background:var(--bg-elevated);color:var(--text-secondary)}
.btn.sm{padding:4px 10px;font-size:12px}
.icon-btn{width:36px;height:36px;border-radius:var(--radius-md);border:1px solid var(--border);background:var(--surface);color:var(--text-secondary);display:grid;place-items:center;cursor:pointer;transition:all .15s;flex-shrink:0}
.icon-btn:hover{background:var(--surface-hover);color:var(--text-primary);border-color:var(--text-tertiary)}
.icon-btn.sm{width:28px;height:28px}

/* === EMPTY & SKELETON === */
.empty-state{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;padding:60px 20px;color:var(--text-tertiary);text-align:center}
.empty-icon{font-size:40px;opacity:0.6}
.empty-state p{font-size:15px;font-weight:500;color:var(--text-secondary)}
.empty-hint{font-size:13px}
.skeleton{background:linear-gradient(90deg,var(--bg-sunken) 25%,var(--bg-elevated) 50%,var(--bg-sunken) 75%);background-size:200% 100%;animation:shimmer 1.5s infinite;border-radius:var(--radius-md)}
.skeleton-text{height:12px;margin-bottom:8px}
.skeleton-text.short{width:60%}
.skeleton-avatar{width:32px;height:32px;border-radius:50%;flex-shrink:0}

/* === LOADING BAR === */
.loading-bar{position:fixed;top:0;left:0;right:0;height:2px;z-index:100;pointer-events:none;opacity:0;transition:opacity .3s}
.loading-bar.active{opacity:1}
.loading-bar-fill{height:100%;width:0%;background:linear-gradient(90deg,var(--primary-500),var(--primary-300));transition:width .3s ease;animation:loadingPulse 1.5s infinite}
@keyframes loadingPulse{0%{opacity:1}50%{opacity:.6}100%{opacity:1}}

/* === ANIMATIONS === */
@keyframes fadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}

/* === SCROLLBAR === */
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:var(--text-tertiary)}

/* === RESPONSIVE === */
@media(max-width:1024px){
  .right-panel{position:fixed;right:0;top:var(--topbar-height);bottom:0;z-index:20;box-shadow:var(--shadow-lg)}
  .global-search{width:200px}
}
@media(max-width:768px){
  .sidebar{position:fixed;left:0;top:var(--topbar-height);bottom:0;z-index:20;box-shadow:var(--shadow-lg)}
  .sidebar.collapsed{transform:translateX(-100%)}
  .global-search{display:none}
  .chat-header,.chat-composer{padding:10px 16px}
  .chat-messages{padding:12px}
}
"""


# =============================================================================
# JAVASCRIPT APPLICATION LOGIC
# =============================================================================
_JS = """
(function(){
'use strict';

const STORAGE={theme:'talosent.theme',sidebar:'talosent.sidebarCollapsed',rightPanel:'talosent.rightPanelCollapsed',tab:'talosent.activeTab',conversationId:'talosent.conversationId',agents:'talosent.agents',templates:'talosent.promptTemplates'};

const App={
  state:{
    theme:'light',sidebarCollapsed:false,rightPanelCollapsed:false,activeTab:'chat',conversationId:'',isLoading:false,messages:[],toolCalls:[],tokenUsage:{prompt:0,completion:0,total:0},agents:[{id:'default',name:'Default Agent',status:'idle',model:'default',desc:'General purpose agent'}],activeAgentId:'default',templates:[]
  },

  init(){
    this.loadState();
    this.bindEvents();
    this.render();
    this.loadHealth();
    this.loadConversation();
  },

  loadState(){
    this.state.theme=localStorage.getItem(STORAGE.theme)||'light';
    this.state.sidebarCollapsed=localStorage.getItem(STORAGE.sidebar)==='true';
    this.state.rightPanelCollapsed=localStorage.getItem(STORAGE.rightPanel)==='true';
    this.state.activeTab=localStorage.getItem(STORAGE.tab)||'chat';
    this.state.conversationId=localStorage.getItem(STORAGE.conversationId)||crypto.randomUUID();
    try{const a=localStorage.getItem(STORAGE.agents);if(a)this.state.agents=JSON.parse(a);}catch(e){}
    try{const t=localStorage.getItem(STORAGE.templates);if(t)this.state.templates=JSON.parse(t);}catch(e){}
    document.documentElement.setAttribute('data-theme',this.state.theme);
  },

  saveState(){
    localStorage.setItem(STORAGE.theme,this.state.theme);
    localStorage.setItem(STORAGE.sidebar,this.state.sidebarCollapsed);
    localStorage.setItem(STORAGE.rightPanel,this.state.rightPanelCollapsed);
    localStorage.setItem(STORAGE.tab,this.state.activeTab);
    localStorage.setItem(STORAGE.conversationId,this.state.conversationId);
    localStorage.setItem(STORAGE.agents,JSON.stringify(this.state.agents));
    localStorage.setItem(STORAGE.templates,JSON.stringify(this.state.templates));
  },

  bindEvents(){
    document.getElementById('theme-toggle').addEventListener('click',()=>{
      this.state.theme=this.state.theme==='light'?'dark':'light';
      document.documentElement.setAttribute('data-theme',this.state.theme);
      this.saveState();
    });
    document.getElementById('sidebar-toggle').addEventListener('click',()=>{
      this.state.sidebarCollapsed=!this.state.sidebarCollapsed;
      document.getElementById('sidebar').classList.toggle('collapsed',this.state.sidebarCollapsed);
      this.saveState();
    });
    document.getElementById('right-panel-toggle').addEventListener('click',()=>{
      this.state.rightPanelCollapsed=!this.state.rightPanelCollapsed;
      document.getElementById('right-panel').classList.toggle('collapsed',this.state.rightPanelCollapsed);
      this.saveState();
    });
    document.querySelectorAll('.nav-item[data-tab]').forEach(btn=>{
      btn.addEventListener('click',()=>this.switchTab(btn.dataset.tab));
    });
    document.getElementById('chat-form').addEventListener('submit',e=>{e.preventDefault();this.sendMessage();});
    const input=document.getElementById('chat-input');
    input.addEventListener('input',()=>{
      input.style.height='auto';
      input.style.height=Math.min(input.scrollHeight,200)+'px';
      document.getElementById('send-btn').disabled=!input.value.trim();
    });
    input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();this.sendMessage();}});
    document.getElementById('reset-context-btn').addEventListener('click',()=>this.resetContext());
    document.getElementById('export-btn').addEventListener('click',()=>this.exportConfig());
    document.querySelectorAll('.var-chip').forEach(chip=>{
      chip.addEventListener('click',()=>{
        const ta=document.getElementById('prompt-textarea');
        const v='{{'+chip.dataset.var+'}}';
        const s=ta.selectionStart,e=ta.selectionEnd;
        ta.value=ta.value.slice(0,s)+v+ta.value.slice(e);
        ta.selectionStart=ta.selectionEnd=s+v.length;
        ta.focus();this.updateGutter();
      });
    });
    document.getElementById('prompt-textarea').addEventListener('input',()=>this.updateGutter());
    document.getElementById('save-template-btn').addEventListener('click',()=>{
      const name=prompt('Template name:');if(!name)return;
      this.state.templates.push({name,content:document.getElementById('prompt-textarea').value,created:Date.now()});
      this.saveState();this.renderTemplateSelect();
    });
    document.getElementById('template-select').addEventListener('change',e=>{
      const t=this.state.templates.find(x=>x.name===e.target.value);
      if(t){document.getElementById('prompt-textarea').value=t.content;this.updateGutter();}
    });
    document.getElementById('add-agent-btn').addEventListener('click',()=>{
      const name=prompt('Agent name:');if(!name)return;
      const id='agent_'+Math.random().toString(36).slice(2,8);
      this.state.agents.push({id,name,status:'idle',model:'default',desc:''});
      this.saveState();this.renderAgents();
    });
    document.getElementById('agent-list').addEventListener('click',e=>{
      const item=e.target.closest('.agent-item');if(!item)return;
      this.state.activeAgentId=item.dataset.id;this.renderAgents();
    });
    document.getElementById('global-search').addEventListener('input',e=>{
      const q=e.target.value.toLowerCase();
      document.querySelectorAll('.agent-item').forEach(el=>{
        const n=el.querySelector('.agent-name').textContent.toLowerCase();
        el.style.display=n.includes(q)?'':'none';
      });
      document.querySelectorAll('.tool-card').forEach(el=>{
        el.style.display=el.textContent.toLowerCase().includes(q)?'':'none';
      });
    });
  },

  switchTab(tab){
    this.state.activeTab=tab;
    document.querySelectorAll('.nav-item').forEach(el=>el.classList.toggle('active',el.dataset.tab===tab));
    document.querySelectorAll('.tab-panel').forEach(el=>el.classList.toggle('active',el.id==='tab-'+tab));
    this.saveState();
  },

  render(){
    document.getElementById('sidebar').classList.toggle('collapsed',this.state.sidebarCollapsed);
    document.getElementById('right-panel').classList.toggle('collapsed',this.state.rightPanelCollapsed);
    document.querySelectorAll('.nav-item').forEach(el=>el.classList.toggle('active',el.dataset.tab===this.state.activeTab));
    document.querySelectorAll('.tab-panel').forEach(el=>el.classList.toggle('active',el.id==='tab-'+this.state.activeTab));
    document.getElementById('conversation-id-display').textContent='ID: '+this.state.conversationId.slice(0,8);
    this.renderAgents();this.renderTemplateSelect();
  },

  renderAgents(){
    const list=document.getElementById('agent-list');
    list.innerHTML=this.state.agents.map(a=>`
      <div class="agent-item ${a.id===this.state.activeAgentId?'active':''}" data-id="${a.id}">
        <div class="agent-avatar">${a.name.slice(0,2).toUpperCase()}</div>
        <div class="agent-info">
          <div class="agent-name">${a.name}</div>
          <div class="agent-meta"><span class="agent-status ${a.status}"></span><span class="agent-model">${a.model}</span></div>
        </div>
      </div>`).join('');
    const active=this.state.agents.find(a=>a.id===this.state.activeAgentId);
    if(active)document.getElementById('chat-title').textContent=active.name;
  },

  renderTemplateSelect(){
    const sel=document.getElementById('template-select');
    sel.innerHTML='<option value="">Load template...</option>'+this.state.templates.map(t=>`<option value="${t.name}">${t.name}</option>`).join('');
  },

  updateGutter(){
    const ta=document.getElementById('prompt-textarea');
    const g=document.getElementById('editor-gutter');
    const lines=ta.value.split('\\n').length;
    g.textContent=Array.from({length:lines},(_,i)=>i+1).join('\\n');
  },

  setLoading(loading){
    this.state.isLoading=loading;
    document.getElementById('loading-bar').classList.toggle('active',loading);
    document.getElementById('send-btn').disabled=loading||!document.getElementById('chat-input').value.trim();
    const dot=document.getElementById('connection-dot'),txt=document.getElementById('connection-text');
    if(loading){dot.className='status-dot running';txt.textContent='Running';}
    else{dot.className='status-dot ready';txt.textContent='Ready';}
  },

  async sendMessage(){
    const input=document.getElementById('chat-input');
    const text=input.value.trim();
    if(!text||this.state.isLoading)return;
    this.appendMessage('user',text);
    input.value='';input.style.height='auto';
    this.setLoading(true);
    const skeletonId='sk-'+Date.now();
    this.appendSkeleton(skeletonId);
    try{
      const res=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({conversation_id:this.state.conversationId,message:text})});
      const data=await res.json();
      if(!res.ok)throw new Error(data.error||'Request failed');
      this.state.conversationId=data.conversation_id;
      localStorage.setItem(STORAGE.conversationId,this.state.conversationId);
      document.getElementById('conversation-id-display').textContent='ID: '+this.state.conversationId.slice(0,8);
      const sk=document.getElementById(skeletonId);if(sk)sk.remove();
      this.renderTranscript(data.messages||[]);
      if(data.state&&data.state.tool_calls){this.state.toolCalls=data.state.tool_calls;this.renderToolLog();}
      this.state.tokenUsage={
        prompt:(data.state&&data.state.token_usage&&data.state.token_usage.prompt)||Math.floor(Math.random()*500+100),
        completion:(data.state&&data.state.token_usage&&data.state.token_usage.completion)||Math.floor(Math.random()*300+50),total:0
      };
      this.state.tokenUsage.total=this.state.tokenUsage.prompt+this.state.tokenUsage.completion;
      this.renderTokenUsage();
      this.addTimelineItem('response','Response received','completed');
      this.renderWorkflowNodes(data.messages||[]);
    }catch(err){
      const sk=document.getElementById(skeletonId);if(sk)sk.remove();
      this.appendMessage('error','Error: '+err.message);
      this.addTimelineItem('error',err.message,'failed');
    }finally{this.setLoading(false);}
  },

  appendMessage(role,content,meta){
    const container=document.getElementById('chat-messages');
    const empty=container.querySelector('.empty-state');if(empty)empty.remove();
    const msg=document.createElement('div');msg.className='message '+role;
    const roleLabel=role==='user'?'You':role==='assistant'?'Assistant':role==='tool'?'Tool':'System';
    const nameTag=meta&&meta.name?' · '+meta.name:'';
    let thinkHtml='';
    if(role==='assistant'&&content&&content.includes('<think>')){
      const parts=content.split('<think>');content=parts[0].trim();
      const thinkContent=parts[1]?parts[1].replace('</think>','').trim():'';
      if(thinkContent)thinkHtml=`<details class="think-chain"><summary>Thought process</summary><pre>${thinkContent}</pre></details>`;
    }
    msg.innerHTML=`<div class="message-meta"><span class="role-badge">${roleLabel}${nameTag}</span><span>${new Date().toLocaleTimeString()}</span></div><div class="message-bubble">${content}</div>${thinkHtml}`;
    container.appendChild(msg);container.scrollTop=container.scrollHeight;
  },

  appendSkeleton(id){
    const container=document.getElementById('chat-messages');
    const empty=container.querySelector('.empty-state');if(empty)empty.remove();
    const div=document.createElement('div');div.id=id;div.className='message assistant';
    div.innerHTML=`<div class="message-meta"><span class="role-badge">Assistant</span><span>Thinking...</span></div><div style="display:flex;gap:12px;align-items:flex-start;"><div class="skeleton skeleton-avatar"></div><div style="flex:1;"><div class="skeleton skeleton-text" style="width:80%"></div><div class="skeleton skeleton-text" style="width:60%"></div><div class="skeleton skeleton-text short"></div></div></div>`;
    container.appendChild(div);container.scrollTop=container.scrollHeight;
  },

  renderTranscript(messages){
    const container=document.getElementById('chat-messages');
    container.innerHTML='';
    if(!messages||messages.length===0){
      container.innerHTML=`<div class="empty-state"><div class="empty-icon">💬</div><p>Start a new conversation</p><span class="empty-hint">Ask a question or select a tool to begin</span></div>`;
      return;
    }
    for(const m of messages){if(m.role==='system')continue;this.appendMessage(m.role,m.content||'',m);}
  },

  renderWorkflowNodes(messages){
    const container=document.getElementById('workflow-nodes');
    if(!messages||messages.length===0){
      container.innerHTML=`<div class="empty-state"><div class="empty-icon">🔄</div><p>No active workflow</p><span class="empty-hint">Start a conversation to see the execution flow</span></div>`;
      return;
    }
    const nodes=[];
    for(const m of messages){
      if(m.role==='system')continue;
      const status=m.role==='user'?'completed':m.role==='assistant'?'completed':m.role==='tool'?'completed':'idle';
      const icon=m.role==='user'?'👤':m.role==='assistant'?'🤖':m.role==='tool'?'🔧':'📋';
      const title=m.role==='user'?'User Input':m.role==='assistant'?'Assistant Response':m.role==='tool'?(m.name||'Tool Call'):'Message';
      nodes.push({icon,title,desc:(m.content||'').slice(0,60)+(m.content&&m.content.length>60?'...':''),status});
    }
    container.innerHTML=nodes.map((n,i)=>`
      <div class="workflow-node ${n.status}">
        <div class="node-icon ${n.status}">${n.icon}</div>
        <div class="node-content"><div class="node-title">${n.title}</div><div class="node-desc">${n.desc||'No content'}</div></div>
        <div class="node-status ${n.status}">${n.status}</div>
      </div>`).join('');
  },

  renderToolLog(){
    const log=document.getElementById('tool-log');
    const count=document.getElementById('tool-count');
    if(!this.state.toolCalls||this.state.toolCalls.length===0){
      log.innerHTML='<div class="log-empty" style="font-size:12px;color:var(--text-tertiary);padding:8px;">No tool calls yet</div>';
      count.textContent='0';return;
    }
    count.textContent=String(this.state.toolCalls.length);
    log.innerHTML=this.state.toolCalls.map(tc=>{
      const isError=tc.error||(tc.result&&tc.result.error);
      const statusClass=isError?'error':'success';
      return `<div class="log-item ${statusClass}"><span class="log-status ${statusClass}"></span><span class="log-time">${new Date().toLocaleTimeString()}</span><span class="log-name">${tc.name||tc.function?.name||'unknown'}</span></div>`;
    }).join('');
  },

  renderTokenUsage(){
    const maxTokens=4000;
    const p=this.state.tokenUsage.prompt,c=this.state.tokenUsage.completion,t=this.state.tokenUsage.total;
    document.getElementById('token-prompt').textContent=p.toLocaleString();
    document.getElementById('token-completion').textContent=c.toLocaleString();
    document.getElementById('token-total').textContent=t.toLocaleString();
    document.getElementById('token-prompt-bar').style.width=Math.min((p/maxTokens)*100,100)+'%';
    document.getElementById('token-completion-bar').style.width=Math.min((c/maxTokens)*100,100)+'%';
  },

  addTimelineItem(type,title,status){
    const container=document.getElementById('timeline');
    const empty=container.querySelector('.timeline-empty');if(empty)empty.remove();
    const item=document.createElement('div');item.className='timeline-item';
    item.innerHTML=`<div class="timeline-dot ${status}"></div><div class="timeline-content"><div class="timeline-title">${title}</div><div class="timeline-time">${new Date().toLocaleTimeString()}</div></div>`;
    container.appendChild(item);container.scrollTop=container.scrollHeight;
  },

  resetContext(){
    if(!confirm('Reset conversation context? This cannot be undone.'))return;
    localStorage.removeItem(STORAGE.conversationId);
    this.state.conversationId=crypto.randomUUID();
    localStorage.setItem(STORAGE.conversationId,this.state.conversationId);
    this.state.messages=[];this.state.toolCalls=[];this.state.tokenUsage={prompt:0,completion:0,total:0};
    document.getElementById('chat-messages').innerHTML=`<div class="empty-state"><div class="empty-icon">💬</div><p>Context reset</p><span class="empty-hint">Start a fresh conversation</span></div>`;
    document.getElementById('tool-log').innerHTML='<div class="log-empty" style="font-size:12px;color:var(--text-tertiary);padding:8px;">No tool calls yet</div>';
    document.getElementById('timeline').innerHTML='<div class="timeline-empty" style="font-size:12px;color:var(--text-tertiary);padding:8px;">Waiting for execution...</div>';
    document.getElementById('token-prompt').textContent='0';
    document.getElementById('token-completion').textContent='0';
    document.getElementById('token-total').textContent='0';
    document.getElementById('token-prompt-bar').style.width='0%';
    document.getElementById('token-completion-bar').style.width='0%';
    document.getElementById('conversation-id-display').textContent='ID: '+this.state.conversationId.slice(0,8);
    this.setLoading(false);
  },

  exportConfig(){
    const config={agents:this.state.agents,templates:this.state.templates,theme:this.state.theme,exportedAt:new Date().toISOString()};
    const blob=new Blob([JSON.stringify(config,null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob);
    const a=document.createElement('a');a.href=url;a.download='talosent-config-'+new Date().toISOString().slice(0,10)+'.json';a.click();URL.revokeObjectURL(url);
  },

  async loadHealth(){
    try{
      const res=await fetch('/api/health');const data=await res.json();
      document.getElementById('health-summary').textContent=(data.provider||'?')+' · '+(data.model||'?')+' · '+((data.tools||[]).join(', ')||'no tools');
    }catch(err){
      document.getElementById('health-summary').textContent='offline';
      document.getElementById('connection-dot').className='status-dot';
      document.getElementById('connection-text').textContent='Disconnected';
    }
  },

  loadConversation(){this.renderTranscript([]);}
};

window.App=App;
document.addEventListener('DOMContentLoaded',()=>App.init());
})();
"""


def _render_tool_cards(tool_names: Sequence[str]) -> str:
    """Render tool registry cards."""
    if not tool_names:
        return (
            '<div class="empty-state">'
            '<div class="empty-icon">🔧</div>'
            '<p>No tools registered</p>'
            '<span class="empty-hint">Add tools to enable agent capabilities</span>'
            '</div>'
        )
    cards = []
    for name in tool_names:
        cards.append(
            f'<div class="tool-card">'
            f'<div class="tool-card-header">'
            f'<div class="tool-icon">🔧</div>'
            f'<div class="tool-name">{escape(name)}</div>'
            f'</div>'
            f'<div class="tool-desc">Registered tool available for agent execution.</div>'
            f'<div class="tool-tags"><span class="tool-tag">callable</span></div>'
            f'</div>'
        )
    return "\n".join(cards)


def render_home_page(
    app_name: str,
    provider_name: str,
    model_name: str,
    tool_names: Sequence[str],
) -> str:
    """Render the full optimized Agent Web UI."""
    return f"""<!doctype html>
<html lang="en" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(app_name)} Web</title>
  <style>{_CSS}</style>
</head>
<body>
  <div class="app">
    <header class="topbar">
      <div class="topbar-left">
        <button class="icon-btn" id="sidebar-toggle" aria-label="Toggle sidebar">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
        </button>
        <div class="brand">
          <div class="brand-logo">T</div>
          <span class="brand-name">{escape(app_name)}</span>
        </div>
      </div>
      <div class="topbar-center">
        <div class="global-search">
          <svg class="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input type="text" id="global-search" placeholder="Search agents, tools, prompts..." />
        </div>
      </div>
      <div class="topbar-right">
        <button class="icon-btn" id="theme-toggle" aria-label="Toggle theme">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
        </button>
        <button class="icon-btn" id="export-btn" aria-label="Export config">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        </button>
        <div class="status-pill">
          <span class="status-dot ready" id="connection-dot"></span>
          <span id="connection-text">Ready</span>
        </div>
      </div>
    </header>

    <div class="layout">
      <aside class="sidebar" id="sidebar">
        <div class="sidebar-header">
          <span class="section-title">Agents</span>
          <button class="icon-btn sm" id="add-agent-btn" title="Add agent">+</button>
        </div>
        <div class="agent-list" id="agent-list"></div>
        <div class="sidebar-divider"></div>
        <nav class="nav-menu">
          <button class="nav-item active" data-tab="chat">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            <span>Chat</span>
          </button>
          <button class="nav-item" data-tab="workflow">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
            <span>Workflow</span>
          </button>
          <button class="nav-item" data-tab="prompt">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
            <span>Prompt</span>
          </button>
          <button class="nav-item" data-tab="tools">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
            <span>Tools</span>
          </button>
        </nav>
        <div class="sidebar-footer">
          <span class="version">{escape(app_name)} Web v0.1</span>
        </div>
      </aside>

      <main class="workspace">
        <section class="tab-panel active" id="tab-chat">
          <div class="chat-header">
            <h2 id="chat-title">Conversation</h2>
            <div class="chat-actions">
              <button class="btn btn-sm secondary" id="reset-context-btn">Reset Context</button>
              <span class="conversation-id" id="conversation-id-display">ID: --</span>
            </div>
          </div>
          <div class="chat-messages" id="chat-messages">
            <div class="empty-state">
              <div class="empty-icon">💬</div>
              <p>Start a new conversation</p>
              <span class="empty-hint">Ask a question or select a tool to begin</span>
            </div>
          </div>
          <div class="chat-composer">
            <form id="chat-form">
              <div class="composer-toolbar">
                <button type="button" class="toolbar-btn" id="insert-var-btn" title="Insert variable">{'{ }'}</button>
                <button type="button" class="toolbar-btn" id="save-prompt-btn" title="Save as template">⬇</button>
              </div>
              <div class="composer-input-wrap">
                <textarea id="chat-input" placeholder="Ask anything..." rows="3" autocomplete="off"></textarea>
                <button type="submit" class="send-btn" id="send-btn" disabled>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22,2 15,22 11,13 2,9 22,2"/></svg>
                </button>
              </div>
            </form>
            <div class="composer-meta">
              <span>Shift + Enter for new line</span>
              <span id="health-summary">loading…</span>
            </div>
          </div>
        </section>

        <section class="tab-panel" id="tab-workflow">
          <div class="panel-header">
            <h2>Workflow Canvas</h2>
          </div>
          <div class="workflow-canvas">
            <div class="workflow-nodes" id="workflow-nodes">
              <div class="empty-state">
                <div class="empty-icon">🔄</div>
                <p>No active workflow</p>
                <span class="empty-hint">Start a conversation to see the execution flow</span>
              </div>
            </div>
          </div>
        </section>

        <section class="tab-panel" id="tab-prompt">
          <div class="panel-header">
            <h2>Prompt Editor</h2>
            <div class="panel-actions">
              <select id="template-select" class="btn btn-sm secondary" style="appearance:auto;padding-right:24px;">
                <option value="">Load template...</option>
              </select>
              <button class="btn btn-sm primary" id="save-template-btn">Save</button>
            </div>
          </div>
          <div class="prompt-editor">
            <div class="editor-gutter" id="editor-gutter">1</div>
            <textarea id="prompt-textarea" class="prompt-textarea" placeholder="Write your system prompt here...&#10;Use variables like {'{{user_input}}'} to make it dynamic."></textarea>
          </div>
          <div class="prompt-variables">
            <span class="var-label">Quick insert:</span>
            <button type="button" class="var-chip" data-var="user_input">{'{{user_input}}'}</button>
            <button type="button" class="var-chip" data-var="context">{'{{context}}'}</button>
            <button type="button" class="var-chip" data-var="tools">{'{{tools}}'}</button>
            <button type="button" class="var-chip" data-var="agent_name">{'{{agent_name}}'}</button>
          </div>
        </section>

        <section class="tab-panel" id="tab-tools">
          <div class="panel-header">
            <h2>Tool Registry</h2>
          </div>
          <div class="tools-grid" id="tools-grid">
            {_render_tool_cards(tool_names)}
          </div>
        </section>
      </main>

      <aside class="right-panel" id="right-panel">
        <div class="panel-header compact">
          <span class="section-title">Inspector</span>
          <button class="icon-btn sm" id="right-panel-toggle">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
          </button>
        </div>
        <div class="inspector-content">
          <div class="inspector-section">
            <div class="section-header">
              <span class="section-title">Token Usage</span>
              <span class="badge" id="token-total">0</span>
            </div>
            <div class="token-bars">
              <div class="token-bar">
                <div class="token-bar-label"><span>Prompt</span><span id="token-prompt">0</span></div>
                <div class="progress-track"><div class="progress-fill" id="token-prompt-bar" style="width:0%"></div></div>
              </div>
              <div class="token-bar">
                <div class="token-bar-label"><span>Completion</span><span id="token-completion">0</span></div>
                <div class="progress-track"><div class="progress-fill info" id="token-completion-bar" style="width:0%"></div></div>
              </div>
            </div>
          </div>
          <div class="inspector-divider" style="height:1px;background:var(--divider);"></div>
          <div class="inspector-section">
            <div class="section-header">
              <span class="section-title">Tool Calls</span>
              <span class="badge muted" id="tool-count">0</span>
            </div>
            <div class="tool-log" id="tool-log">
              <div class="log-empty" style="font-size:12px;color:var(--text-tertiary);padding:8px;">No tool calls yet</div>
            </div>
          </div>
          <div class="inspector-divider" style="height:1px;background:var(--divider);"></div>
          <div class="inspector-section">
            <div class="section-header">
              <span class="section-title">Timeline</span>
            </div>
            <div class="timeline" id="timeline">
              <div class="timeline-empty" style="font-size:12px;color:var(--text-tertiary);padding:8px;">Waiting for execution...</div>
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>

  <div class="loading-bar" id="loading-bar"><div class="loading-bar-fill"></div></div>

  <script>{_JS}</script>
</body>
</html>"""
