/* AI Assistant External Script
 * Version: 2025-11-17
 * Purpose: Reliable initialization outside inline template to avoid caching / execution blockers.
 */
(function(){
  const STATE = { messageCount: 0, initialized: false };

  function logReady(msg){ console.log('%c[AI Assistant] ' + msg,'color:#667eea;font-weight:600'); }
  function logError(msg){ console.error('[AI Assistant ERROR] ' + msg); }

  function escapeHtml(text){ const d=document.createElement('div'); d.textContent=text; return d.innerHTML; }
  function formatAIMessage(text){
    return text
      .replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>')
      .replace(/\n/g,'<br>')
      .replace(/✓/g,'<span class="text-success">✓</span>')
      .replace(/☐/g,'<span class="text-muted">☐</span>');
  }

  function appendMessage(sender,text){
    const chatMessages=document.getElementById('chatMessages');
    if(!chatMessages){ logError('chatMessages container missing'); return; }
    const wrap=document.createElement('div'); wrap.className='message-wrapper mb-3';
    const ts=new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
    if(sender==='user'){
      wrap.innerHTML=`<div class="d-flex justify-content-end">\n        <div class="message-content bg-primary text-white rounded-3 p-3" style="max-width:75%;">\n          <p class="mb-0">${escapeHtml(text)}<\/p>\n          <small class="opacity-75 d-block mt-1">${ts}<\/small>\n        <\/div>\n        <div class="avatar bg-secondary text-white rounded-circle ms-3 flex-shrink-0" style="width:40px;height:40px;display:flex;align-items:center;justify-content:center;">\n          <i class="fas fa-user"><\/i>\n        <\/div>\n      <\/div>`;
    } else {
      wrap.innerHTML=`<div class="d-flex">\n        <div class="avatar bg-primary text-white rounded-circle me-3 flex-shrink-0" style="width:40px;height:40px;display:flex;align-items:center;justify-content:center;">\n          <i class="fas fa-robot"><\/i>\n        <\/div>\n        <div class="message-content bg-light rounded-3 p-3" style="max-width:75%;position:relative;">\n          <p class="mb-0">${formatAIMessage(text)}<\/p>\n          <div class="d-flex justify-content-between align-items-center mt-1">\n             <small class="text-muted">${ts}<\/small>\n             <span class="badge bg-info text-dark kb-source-badge" style="display:none;" title="Knowledge Base Source">KB<\/span>\n          <\/div>\n        <\/div>\n      <\/div>`;
    }
    chatMessages.appendChild(wrap); chatMessages.scrollTop=chatMessages.scrollHeight;
  }

  function showTyping(){
    const chatMessages=document.getElementById('chatMessages');
    if(!chatMessages) return;
    const indicator=document.createElement('div');
    indicator.id='typingIndicator'; indicator.className='message-wrapper mb-3';
    indicator.innerHTML=`<div class="d-flex">\n      <div class="avatar bg-primary text-white rounded-circle me-3 flex-shrink-0" style="width:40px;height:40px;display:flex;align-items:center;justify-content:center;">\n        <i class="fas fa-robot"><\/i>\n      <\/div>\n      <div class="message-content bg-light rounded-3 p-3">\n        <div class="typing-dots"><span><\/span><span><\/span><span><\/span><\/div>\n      <\/div>\n    <\/div>`;
    chatMessages.appendChild(indicator); chatMessages.scrollTop=chatMessages.scrollHeight;
  }
  function hideTyping(){ const i=document.getElementById('typingIndicator'); if(i) i.remove(); }

  function generateFallback(userMessage){
    const lower=userMessage.toLowerCase();
    if(/technical approach|technical|approach/.test(lower)) return 'Outline your technical approach with methodology, staffing, schedule, QA, transition plan. Want a section-by-section template?';
    if(/past performance|references|experience/.test(lower)) return 'Include 3-5 relevant contracts: client, value, scope, metrics, contact. Need a reference format?';
    if(/pric|cost|bid/.test(lower)) return 'Pricing: Labor 70-80%, Supplies 5-10%, Equip amortized, Overhead 15-20%, Profit 8-12%. Want calculator guidance?';
    if(/compliance|matrix|requirements/.test(lower)) return 'Build a compliance matrix mapping each RFP clause to proposal sections. I can generate a starter layout.';
    if(/deadline|last minute|emergency|urgent/.test(lower)) return 'Deadline triage: forms, pricing, past performance, technical completeness, submission prep. Need a priority checklist?';
    return 'Give me more context (contract type, challenge) and I will tailor guidance.';
  }

  function applySourceBadges(){ const badges=document.querySelectorAll('.kb-source-badge'); if(badges.length) badges[badges.length-1].style.display='inline-block'; }

  function sendMessage(event){
    if(event && event.preventDefault) event.preventDefault();
    const input=document.getElementById('userMessage'); if(!input){ logError('userMessage input missing'); return; }
    const rawValue = input.value || '';
    const message=(rawValue).trim();
    console.log('[AI Assistant] sendMessage invoked. Raw length:', rawValue.length, 'Trimmed empty?:', !message);
    if(!message){ console.warn('[AI Assistant] Ignoring empty message submit'); return; }
    if(STATE.messageCount===0){ const qs=document.getElementById('quickStartButtons'); if(qs) qs.style.display='none'; }
    STATE.messageCount++;
    appendMessage('user', message); input.value=''; showTyping();
    const role=document.getElementById('assistantRole')?.value || '';
    console.log('[AI Assistant] Fetching reply. Role="'+role+'" Message="'+message.slice(0,80)+'"');
    fetch('/api/ai-assistant-reply', {
      method:'POST',
      headers:{'Content-Type':'application/json','Accept':'application/json'},
      credentials:'same-origin',
      body:JSON.stringify({message, role})
    }).then(r=>{
      if(!r.ok){ return r.text().then(t=>{ throw new Error('HTTP '+r.status+': '+t); }); }
      return r.json();
    }).then(data=>{
      hideTyping();
      if(data && data.success){
        let txt=data.answer||''; if(data.followups){ txt+=`\n\n<em>Related prompts:</em> ${escapeHtml(data.followups)}`; }
        console.log('[AI Assistant] Success response received. Answer length:', txt.length);
        appendMessage('ai', txt);
      } else {
        console.warn('[AI Assistant] Non-success response. Using fallback.');
        appendMessage('ai', generateFallback(message));
      }
    }).then(()=> setTimeout(applySourceBadges,60))
      .catch(err=>{ hideTyping(); logError('Fetch error: '+err.message); appendMessage('ai', generateFallback(message)); });
  }

  // Expose globally
  window.sendMessage = sendMessage;
  window.askQuestion = function(q){ const input=document.getElementById('userMessage'); if(input){ input.value=q; sendMessage(); }};

  function bind(){
    if(STATE.initialized) return;
    const form=document.getElementById('chatForm');
    const btn=document.getElementById('sendButton');
    if(form){ form.addEventListener('submit', sendMessage); } else { logError('chatForm not found'); }
    if(btn){ btn.addEventListener('click', function(e){ e.preventDefault(); sendMessage(e); }); }
    // Enter key
    const input=document.getElementById('userMessage');
    if(input){ input.addEventListener('keydown', e=>{ if(e.key==='Enter'){ e.preventDefault(); sendMessage(e); }}); }
    // Diagnostic badge
    const container=document.querySelector('#chatForm')?.closest('.card');
    if(container){ const diag=document.createElement('div'); diag.className='small text-muted mt-2'; diag.id='aiDiag'; diag.textContent='Assistant ready'; container.appendChild(diag); }
    logReady('Initialized (external script)');
    STATE.initialized=true;
  }

  function init(){ if(document.getElementById('chatForm')){ bind(); } else { setTimeout(init,100); } }
  if(document.readyState==='loading'){ document.addEventListener('DOMContentLoaded', init); } else { init(); }
})();
