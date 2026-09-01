/* ==========================================================================
   IBM Carbon report kit - behaviour
   Lifted verbatim from the [CLIENT SITE] O2C artifact house format.

   Six progressive enhancements, all selector-driven - drop the file in and
   anything matching the selectors below animates. No dependencies, no CDN.

     1. reveal on scroll        .kpi .pain-card .enh-card .wave .block table
     2. bar fill on view        .bar[data-w]
     3. KPI count-up            .kpi .num
     4. live table filter       tables above a row threshold
     5. SVG zoom controls       .svgwrap > svg
     6. click-drag pan          .svgwrap

   Every animation carries a failsafe timeout. A client opens this in an old
   browser, or prints it, and the observer never fires - without the failsafe
   the page renders blank rows and empty bars. Keep them.
   ========================================================================== */

(function(){
  var d=document;
  function all(s,r){return Array.prototype.slice.call((r||d).querySelectorAll(s));}

  /* --- reveal on scroll ---------------------------------------------- */
  var io=null;
  if('IntersectionObserver' in window){
    d.body.classList.add('anim');
    /* failsafe: whatever happens, nothing stays hidden */
    setTimeout(function(){ d.body.classList.remove('anim'); }, 2500);
    io=new IntersectionObserver(function(es){
      es.forEach(function(e){ if(e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target);} });
    },{rootMargin:'0px 0px -8% 0px',threshold:.05});
    all('.kpi,.pain-card,.enh-card,.wave,.block,table').forEach(function(el){
      el.classList.add('reveal'); io.observe(el);
    });
  }

  /* --- maturity bars fill when seen ---------------------------------- */
  var bars=all('.bar');
  if(bars.length){
    var bo=('IntersectionObserver' in window)?new IntersectionObserver(function(es){
      es.forEach(function(e){ if(e.isIntersecting){
        e.target.style.width=(e.target.getAttribute('data-w')||'0')+'px'; bo.unobserve(e.target);} });
    },{threshold:.3}):null;
    bars.forEach(function(b){
      var w=b.getAttribute('data-w')||b.style.width.replace('px','');
      b.setAttribute('data-w',w); b.style.width='0px';
      if(bo){bo.observe(b);} else {b.style.width=w+'px';}
    });
    /* failsafe: a bar must never be left empty */
    setTimeout(function(){ bars.forEach(function(b){
      if(!b.style.width||b.style.width==='0px'){ b.style.width=(b.getAttribute('data-w')||0)+'px'; }
    }); }, 2500);
  }

  /* --- KPI count-up --------------------------------------------------- */
  all('.kpi .num').forEach(function(n){
    var t=n.textContent.trim(), m=t.match(/^(\d+(?:\.\d+)?)(.*)$/);
    if(!m) return;
    var target=parseFloat(m[1]), suffix=m[2], dec=(m[1].split('.')[1]||'').length, started=false;
    function run(){
      if(started) return; started=true;
      var t0=null, dur=850;
      function step(ts){ if(!t0)t0=ts; var p=Math.min((ts-t0)/dur,1);
        var e=1-Math.pow(1-p,3);
        n.textContent=(target*e).toFixed(dec)+suffix;
        if(p<1) requestAnimationFrame(step); else n.textContent=m[1]+suffix; }
      requestAnimationFrame(step);
    }
    if('IntersectionObserver' in window){
      new IntersectionObserver(function(es,o){es.forEach(function(e){
        if(e.isIntersecting){run(); o.disconnect();}});},{threshold:.5}).observe(n);
    } else { run(); }
  });

  /* --- scroll-spy on the section strip -------------------------------- */
  var links=all('.secnav a'), heads=all('h2[id]');
  if(links.length&&heads.length){
    var spy=function(){
      var y=window.scrollY+120, cur=heads[0];
      heads.forEach(function(h){ if(h.offsetTop<=y) cur=h; });
      links.forEach(function(a){
        a.classList.toggle('active', a.getAttribute('href')==='#'+cur.id);
      });
    };
    window.addEventListener('scroll',spy,{passive:true}); spy();
  }

  /* --- collapsible sections ------------------------------------------- */
  heads.forEach(function(h){
    if(h.closest('.hero')) return;
    h.classList.add('collapsible');
    h.setAttribute('role','button'); h.setAttribute('tabindex','0');
    var kids=[],n=h.nextElementSibling;
    while(n&&n.tagName!=='H2'&&!n.classList.contains('footer')){kids.push(n);n=n.nextElementSibling;}
    function toggle(){
      var closed=h.classList.toggle('closed');
      kids.forEach(function(k){k.style.display=closed?'none':'';});
    }
    h.addEventListener('click',toggle);
    h.addEventListener('keydown',function(e){
      if(e.key==='Enter'||e.key===' '){e.preventDefault();toggle();}});
  });

  /* --- severity filter over pain cards -------------------------------- */
  /* Scoped to the band the chips sit in. A page can carry more than one row of
     .pain-card - findings in one row, root causes in another - and a bar that
     silently governed a band it does not sit above would hide the wrong cards:
     pressing Medium would blank the findings and reveal the causes. */
  var seed=all('.pain-card')[0], host=seed?seed.parentNode:null;
  var cards=host?all('.pain-card',host):[];
  if(cards.length>3){
    var bar=d.createElement('div');
    bar.className='ctl on';
    bar.innerHTML='<span class="ctl-lbl">Severity</span>'+
      '<button class="chip" data-f="all" aria-pressed="true">All</button>'+
      '<button class="chip" data-f="critical" aria-pressed="false">High</button>'+
      '<button class="chip" data-f="mid" aria-pressed="false">Medium</button>'+
      '<button class="chip" data-f="low" aria-pressed="false">Low</button>'+
      '<span class="count"></span>';
    host.insertBefore(bar,cards[0]);
    var cnt=bar.querySelector('.count');
    function sev(c){return c.classList.contains('critical')?'critical':
                    c.classList.contains('low')?'low':'mid';}
    function apply(f){
      var shown=0;
      cards.forEach(function(c){
        var ok=(f==='all')||sev(c)===f;
        c.style.display=ok?'':'none'; if(ok)shown++;
      });
      cnt.textContent=shown+' of '+cards.length+' shown';
      all('.chip',bar).forEach(function(b){
        b.setAttribute('aria-pressed', String(b.getAttribute('data-f')===f));});
    }
    all('.chip',bar).forEach(function(b){
      b.addEventListener('click',function(){apply(b.getAttribute('data-f'));});});
    apply('all');
  }

  /* --- text filter on long tables ------------------------------------- */
  all('table').forEach(function(t){
    var rows=all('tbody tr',t);
    if(rows.length<8) return;
    var bar=d.createElement('div'); bar.className='ctl on';
    var inp=d.createElement('input');
    inp.className='tfilter'; inp.type='search';
    inp.placeholder='Filter these '+rows.length+' rows…';
    var cnt=d.createElement('span'); cnt.className='count';
    bar.appendChild(inp); bar.appendChild(cnt);
    t.parentNode.insertBefore(bar,t);
    inp.addEventListener('input',function(){
      var q=inp.value.toLowerCase().trim(), shown=0;
      rows.forEach(function(r){
        var ok=!q||r.textContent.toLowerCase().indexOf(q)>-1;
        r.classList.toggle('hidden-row',!ok); if(ok)shown++;
      });
      cnt.textContent=q?(shown+' of '+rows.length):'';
    });
  });

  /* --- svg zoom -------------------------------------------------------- */
  all('.svgwrap').forEach(function(w){
    var svg=w.querySelector('svg'); if(!svg) return;
    var z=1;
    var ctl=d.createElement('div'); ctl.className='zoomctl on';
    ctl.innerHTML='<button class="chip" data-z="out">&#8722;</button>'+
                  '<button class="chip" data-z="reset">Fit</button>'+
                  '<button class="chip" data-z="in">&#43;</button>'+
                  '<span class="count">drag to pan</span>';
    w.parentNode.insertBefore(ctl,w);
    all('.chip',ctl).forEach(function(b){
      b.addEventListener('click',function(){
        var k=b.getAttribute('data-z');
        z = k==='in'?Math.min(z*1.25,3) : k==='out'?Math.max(z/1.25,.4) : 1;
        svg.style.transform='scale('+z+')';
      });
    });
    var down=false,sx=0,sy=0,l=0,tp=0;
    w.addEventListener('mousedown',function(e){down=true;sx=e.pageX;sy=e.pageY;
      l=w.scrollLeft;tp=w.scrollTop;w.style.cursor='grabbing';});
    window.addEventListener('mouseup',function(){down=false;w.style.cursor='';});
    w.addEventListener('mousemove',function(e){ if(!down)return; e.preventDefault();
      w.scrollLeft=l-(e.pageX-sx); w.scrollTop=tp-(e.pageY-sy);});
  });
})();

/* ==========================================================================
   print-correctness addendum

   A headless print of a finished deliverable showed every KPI tile rendering
   as 0. The count-up above is the one animation with no failsafe: reveal and
   the bars each snap to their final state after 2.5s, the numbers do not, so
   a tile that was never scrolled into view prints as whatever the animation
   had reached - which on a print job is zero.

   This block runs synchronously straight after the kit script. IntersectionObserver
   callbacks are always asynchronous, so the tile text is still the authored value
   at this point and can be captured safely.

   It then restores that value, fills the bars, reveals hidden blocks and expands
   any collapsed section whenever the page is about to print, and once on a timer
   as a backstop for browsers with no beforeprint event.
   ========================================================================== */
(function(){
  var d=document;
  function all(s){return Array.prototype.slice.call(d.querySelectorAll(s));}

  /* capture the authored numbers before anything animates them */
  all('.kpi .num').forEach(function(n){
    if(n.getAttribute('data-target')===null){
      n.setAttribute('data-target', n.textContent.trim());
    }
  });

  function settle(){
    d.body.classList.remove('anim');
    all('.reveal').forEach(function(e){ e.classList.add('in'); });
    all('.bar').forEach(function(b){
      var w=b.getAttribute('data-w');
      if(w) b.style.width=w+'px';
    });
    all('.kpi .num').forEach(function(n){
      var t=n.getAttribute('data-target');
      if(t) n.textContent=t;
    });
    all('h2.collapsible.closed').forEach(function(h){
      h.classList.remove('closed');
      var n=h.nextElementSibling;
      while(n && n.tagName!=='H2' && !n.classList.contains('footer')){
        n.style.display=''; n=n.nextElementSibling;
      }
    });
  }

  if(window.matchMedia){
    var mq=window.matchMedia('print');
    if(mq.addEventListener) mq.addEventListener('change',function(e){ if(e.matches) settle(); });
    else if(mq.addListener) mq.addListener(function(e){ if(e.matches) settle(); });
  }
  window.addEventListener('beforeprint', settle);
  /* backstop: a headless render never fires beforeprint */
  setTimeout(settle, 2500);
})();
