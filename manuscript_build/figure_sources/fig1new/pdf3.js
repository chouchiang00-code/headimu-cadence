const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage();
const svg=require('fs').readFileSync(process.argv[2],'utf8');
await p.setContent(`<html><head><style>@page{size:900px 930px;margin:0}html,body{margin:0}</style></head><body>${svg}</body></html>`);
await p.pdf({path:process.argv[3],width:'900px',height:'930px',printBackground:true,pageRanges:'1'});await b.close()})();
