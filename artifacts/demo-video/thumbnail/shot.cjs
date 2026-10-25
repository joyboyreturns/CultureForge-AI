const { createRequire } = require('module');
const { chromium } = createRequire('/Users/vincent/Documents/AccessRipple/package.json')('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1280,height:720}});
await p.goto('file://'+__dirname+'/thumbnail.html');await p.waitForTimeout(800);
await p.screenshot({path:__dirname+'/thumbnail.png'});await b.close();})();
