// ui.js - shared lightweight UI utilities (toast + modal helpers)
(function(){
  if (window.__UI_HELPERS__) return; window.__UI_HELPERS__=true;

  window.showToast = function(message, type='info', timeout=5000){
    try {
      const existing = document.querySelectorAll('.cl-toast');
      if (existing.length > 6) existing[0].remove();
      const div = document.createElement('div');
      div.className = `cl-toast alert alert-${type==='error'?'danger':type} alert-dismissible fade show position-fixed`;
      div.style.cssText = 'top:20px;right:20px;z-index:1080;max-width:420px;';
      div.innerHTML = `\n<button type="button" class="btn-close" data-bs-dismiss="alert"></button>\n<div class="d-flex align-items-start">\n <div class="flex-grow-1 me-2">${message}</div>\n</div>`;
      document.body.appendChild(div);
      setTimeout(()=>{ if(div && div.parentNode){ div.classList.remove('show'); setTimeout(()=>div.remove(),300);} }, timeout);
    } catch(e){ console.warn('showToast failed', e); }
  };

  window.showConfirm = function(message, onYes){ if(confirm(message)){ onYes&&onYes(); } };

})();
