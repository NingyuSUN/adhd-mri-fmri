// Render the delivered PPTX without modifying it. Uses bundled artifact-tool.
import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
const req=createRequire(path.resolve(path.dirname(process.execPath),'../node_modules/__runtime__.cjs'));
const {FileBlob,PresentationFile}=await import(pathToFileURL(req.resolve('@oai/artifact-tool')).href);
const [input,out]=process.argv.slice(2);
if(!input||!out)throw Error('Usage: node render.mjs INPUT.pptx OUTPUT_DIR');
await fs.mkdir(out,{recursive:true});
const p=await PresentationFile.importPptx(await FileBlob.load(input));
for(let i=0;i<p.slides.items.length;i++){
 const blob=await p.export({slide:p.slides.items[i],format:'png',scale:1});
 await fs.writeFile(path.join(out,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await blob.arrayBuffer()));
 console.log(`rendered ${i+1}/${p.slides.items.length}`);
}
