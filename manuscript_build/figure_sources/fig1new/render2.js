const {chromium}=require('playwright');
(async()=>{const [,,inp,out,scale,w,h]=process.argv;const b=await chromium.launch();
const p=await b.newPage({viewport:{width:+w,height:+h},deviceScaleFactor:+(scale||1)});
await p.goto('file://'+require('path').resolve(inp));await p.screenshot({path:out});await b.close()})();
