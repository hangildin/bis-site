import { chromium } from 'playwright';
import fs from 'node:fs';
const base='http://127.0.0.1:8765';
const pages=['index.html','services.html','corporate-events.html','city-events.html','brand-events.html','sports-events.html','children-events.html','projects.html','himfest.html','zelenodolsk.html','kastamonu.html','spartakiada.html','festival-dobryh-del.html','phuket-wedding.html','plehanov-reu.html','letters.html','journal.html','journal-corporate-brief.html','journal-new-year-corporate.html','journal-children-birthday.html','journal-kids-festival-zone.html','journal-city-festival.html','journal-brand-launch.html','journal-company-spartakiad.html','journal-event-budget.html'];
const views=[{name:'desktop',width:1440,height:900},{name:'mobile',width:390,height:844},{name:'tablet',width:768,height:1024},{name:'small-desktop',width:1024,height:768},{name:'small-mobile',width:320,height:700}];
const shots=new Set(['index.html','services.html','children-events.html','corporate-events.html','projects.html','journal.html','journal-children-birthday.html','journal-corporate-brief.html']);
const result=[];
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_BIN||'/usr/bin/google-chrome',args:['--no-sandbox','--disable-dev-shm-usage']});
fs.mkdirSync('artifacts/bis-v2-review',{recursive:true});
for(const v of views){
 const context=await browser.newContext({viewport:{width:v.width,height:v.height},deviceScaleFactor:1,locale:'ru-RU',reducedMotion:'reduce'});
 for(const pageFile of pages){
  const page=await context.newPage(),errors=[],failed=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('response',r=>{if(r.url().startsWith(base)&&r.status()>=400)failed.push(String(r.status())+' '+r.url().replace(base,''))});
  await page.goto(base+'/'+pageFile,{waitUntil:'load',timeout:20000});
  await page.evaluate(async()=>{const step=Math.max(500,Math.floor(window.innerHeight*.75));for(let top=0;top<document.documentElement.scrollHeight;top+=step){window.scrollTo(0,top);await new Promise(r=>setTimeout(r,15));}window.scrollTo(0,0)});
  // Lazy images become visible over long pages; decode them rather than flagging pending loads.
  await page.evaluate(async()=>{
    const imgs=[...document.images];
    await Promise.race([
      Promise.all(imgs.map(img=>{img.loading='eager';return img.decode?.().catch(()=>{})})),
      new Promise(resolve=>setTimeout(resolve,12000))
    ]);
  });
  const audit=await page.evaluate(()=>{
    const doc=document.documentElement,body=document.body;
    const overflow=Math.max(doc.scrollWidth,body.scrollWidth)-window.innerWidth;
    const broken=[...document.images].filter(i=>i.getAttribute('src')&&i.getBoundingClientRect().width>0&&i.complete&&i.naturalWidth===0).map(i=>i.getAttribute('src'));
    const h1=document.querySelectorAll('h1').length;
    const missingLabels=[...document.querySelectorAll('a')].filter(a=>!a.textContent.trim()&&!a.getAttribute('aria-label')&&!a.querySelector('img[alt]')).length;
    const oversized=[...document.querySelectorAll('*')].filter(x=>{const r=x.getBoundingClientRect();return r.width>10&&r.right>window.innerWidth+4&&getComputedStyle(x).position!=='fixed'}).slice(0,18).map(x=>{const r=x.getBoundingClientRect();return x.tagName.toLowerCase()+'.'+String(x.className?.baseVal||x.className||'').slice(0,45)+' ['+Math.round(r.left)+'..'+Math.round(r.right)+'] section='+String(x.closest('section')?.className||'')+' text='+x.textContent.trim().slice(0,55).replaceAll('\n',' ')});
    return {overflow,broken,h1,main:!!document.querySelector('main'),missingLabels,oversized};
  });
  if(shots.has(pageFile)&&v.name!=='small-mobile')await page.screenshot({path:'artifacts/bis-v2-review/'+pageFile.replace('.html','')+'-'+v.name+'.jpg',type:'jpeg',quality:77,fullPage:true,animations:'disabled'});
  result.push({page:pageFile,viewport:v.name,...audit,errors,failed});
  await page.close();
 }
 await context.close();
}
await browser.close();
const critical=result.filter(x=>x.overflow>4||x.broken.length||x.failed.length||x.errors.length||x.h1!==1||!x.main);
fs.writeFileSync('artifacts/bis-v2-review/report.json',JSON.stringify({run:new Date().toISOString(),result,critical},null,2));
const md=['# BIS V2 — Browser & Visual QA','','Checked **'+pages.length+' pages** in **'+views.length+' viewports**.','','| Page | Desktop | Mobile 390px | Tablet 768px | Laptop 1024px | Small 320px |','|---|---|---|---|---|',...pages.map(name=>'| '+name+' | '+views.map(v=>{const x=result.find(x=>x.page===name&&x.viewport===v.name);return x.overflow>4||x.broken.length||x.failed.length||x.errors.length||x.h1!==1||!x.main?'❌':'✅'}).join(' | ')+' |'),'', '**Errors:** '+critical.length,...critical.slice(0,40).map(x=>'- '+x.page+' / '+x.viewport+': overflow '+x.overflow+'px, images '+x.broken.join(', ')+' HTTP '+x.failed.join(', ')+' JS '+x.errors.join('; ')+' H1 '+x.h1+' extras '+x.oversized.join(', ')), '', 'The GitHub Actions artifact bis-v2-review contains full-page screenshots. This workflow does not deploy or edit main.'].join('\n');
if(process.env.GITHUB_STEP_SUMMARY)fs.appendFileSync(process.env.GITHUB_STEP_SUMMARY,md+'\n');
console.log(md);
if(critical.length)process.exitCode=1;
