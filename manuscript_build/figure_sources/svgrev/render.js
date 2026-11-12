const {chromium}=require('playwright');
(async()=>{const [,,inp,out,scale]=process.argv;const b=await chromium.launch();
const p=await b.newPage({viewport:{width:1448,height:1086},deviceScaleFactor:+(scale||1)});
await p.goto('file://'+require('path').resolve(inp));await p.screenshot({path:out});await b.close()})();
