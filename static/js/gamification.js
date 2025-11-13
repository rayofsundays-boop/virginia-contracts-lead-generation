// Shared Gamification Functions
// Loaded on user-facing lead/pricing/dashboard pages. Safe no-ops if markup absent.
(function(){
  if (window.__GAMIFICATION_LOADED__) return; // prevent double load
  window.__GAMIFICATION_LOADED__ = true;

  function getEl(id){ return document.getElementById(id); }

  window.updateActivityScore = function(points, action){
    try {
      const scoreEl = getEl('activityScore');
      if (!scoreEl) return; // page not showing gamification metrics
      let current = parseInt(scoreEl.textContent) || 0;
      current += (points||0);
      scoreEl.textContent = current;

      // Animate
      scoreEl.classList.add('gam-score-bump');
      setTimeout(()=> scoreEl && scoreEl.classList.remove('gam-score-bump'), 350);

      // Action counters
      const map = { 'view':'viewedCount', 'save':'savedCount', 'inquiry':'inquiriesCount' };
      const targetId = map[action];
      if (targetId){
        const el = getEl(targetId);
        if (el){ el.textContent = (parseInt(el.textContent)||0) + 1; }
      }
      const todayEl = getEl('todayActionsCount');
      if (todayEl){
        // Recompute from individual counters if available
        const v = parseInt(getEl('viewedCount')?.textContent||0);
        const s = parseInt(getEl('savedCount')?.textContent||0);
        const i = parseInt(getEl('inquiriesCount')?.textContent||0);
        todayEl.textContent = v + s + i;
      }

      // Persist minimal stats
      const stats = JSON.parse(localStorage.getItem('userStats')||'{}');
      stats.score = current;
      localStorage.setItem('userStats', JSON.stringify(stats));
      // Optional debug
      // console.debug('[Gamification] +' + points + ' for', action);
    } catch(e){ console.warn('updateActivityScore error', e); }
  };

  window.showAchievement = function(title, description, icon){
    const toast = document.getElementById('achievementToast');
    if (!toast) return;
    const t = toast.querySelector('.achievement-title'); if (t) t.textContent = title || 'Achievement';
    const d = toast.querySelector('.achievement-desc'); if (d) d.textContent = description || '';
    const i = toast.querySelector('.achievement-icon'); if (i) i.textContent = icon || '⭐';
    toast.style.display = 'block';
    updateActivityScore(100, 'achievement');
    setTimeout(()=>{ if (toast) toast.style.display='none'; }, 3500);
  };

  window.checkAndShowAchievement = function(){
    const hour = new Date().getHours();
    if (hour < 9 && !sessionStorage.getItem('earlyBirdShown')){
      setTimeout(()=>{ showAchievement('Early Bird','Logged in before 9 AM','🌅'); }, 2000);
      sessionStorage.setItem('earlyBirdShown','true');
    }
  };

  // Lightweight style for bump effect
  const style = document.createElement('style');
  style.textContent = '.gam-score-bump{transition:transform .25s,color .25s; transform:scale(1.2); color:#28a745 !important;}';
  document.head.appendChild(style);

  // Auto-init if score element present
  document.addEventListener('DOMContentLoaded', ()=>{
    if (document.getElementById('activityScore')){
      checkAndShowAchievement();
    }
  });
})();
