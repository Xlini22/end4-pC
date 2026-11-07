"""Build a standalone WebGL view of the patched native shader. Usage: preview.py SOURCE_DIR OUTPUT.html [BACKGROUND_IMAGE]"""
import base64
import json
import mimetypes
from pathlib import Path
import re
import sys

source = (Path(sys.argv[1]) / 'src/Shaders.hpp').read_text()
shader = re.search(r'\{"liquidglass.frag", R"GLSL\((.*?)\)GLSL"\}', source, re.S).group(1).strip()
# Only remap input coordinates: the refraction and shading are the native shader.
shader = shader.replace('precision highp float;', 'precision highp float;\nuniform vec2 origin;\nuniform vec2 sceneSize;', 1)
shader = shader.replace('return wuv * (1.0 - 2.0 * uvPadding) + uvPadding;', 'return (wuv * fullSize + origin) / sceneSize;')
shader = shader.replace('return (wuv * (1.0 - 2.0 * uvPadding) + uvPadding) * sampleUVScale + sampleUVOffset;', 'return (wuv * fullSize + origin) / sceneSize;')
background = Path(sys.argv[3]) if len(sys.argv) > 3 else Path(__file__).resolve().parents[3] / 'assets/images/default_wallpaper.png'
image_url = 'data:' + (mimetypes.guess_type(background.name)[0] or 'image/png') + ';base64,' + base64.b64encode(background.read_bytes()).decode()
html = r'''<!doctype html>
<html lang="it"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Prova della rifrazione Glassy</title>
<style>
:root{color-scheme:dark;font:15px system-ui;background:#171b20;color:#eef2f5}body{max-width:1100px;margin:28px auto;padding:0 20px}h1{font-size:24px;margin:0 0 8px}p{color:#c0cbd3;line-height:1.5}canvas{display:block;width:100%;border-radius:12px;touch-action:none;cursor:grab}canvas:active{cursor:grabbing}.controls{display:flex;gap:18px;flex-wrap:wrap;align-items:center;margin:18px 0}label{display:grid;gap:6px}input[type=range]{width:180px;accent-color:#79d2e5}button,select{font:inherit;padding:9px 14px;border:1px solid #65717c;border-radius:8px;background:#29343e;color:inherit}button:focus-visible,select:focus-visible,input:focus-visible{outline:3px solid #79d2e5;outline-offset:3px}output{font-variant-numeric:tabular-nums}#error{color:#ffb5ae}small{color:#b5c2cb}
</style>
<h1>Prova della rifrazione Glassy</h1>
<p>Trascina il vetro sulla fotografia: il centro resta completamente nitido e senza tinta. La deformazione agisce solo vicino ai bordi. Questa prova usa lo shader nativo candidato e non cambia il desktop.</p>
<div class="controls">
<label>Materiale<select id="material"><option value="clear">Trasparente</option><option value="frosted">Satinato</option></select></label>
<label>Fascia del bordo <output id="widthValue"></output><input id="width" type="range" min="2" max="25" step="1" value="7"></label>
<label>Rifrazione <output id="strengthValue"></output><input id="strength" type="range" min="0" max="200" step="5" value="135"></label>
<label>Sfocatura <output id="blurValue"></output><input id="blur" type="range" min="0" max="20" step="1" value="6"></label>
<label>Immagine di sfondo<input id="photo" type="file" accept="image/*"></label>
<button id="motion" aria-pressed="false">Avvia movimento</button><button id="reset">Ripristina</button>
</div>
<canvas id="view" width="1100" height="540" tabindex="0" aria-label="Prova del vetro: trascina con il mouse o sposta il riquadro con le frecce"></canvas>
<p id="error" role="alert"></p><small>La fascia è una percentuale del lato corto, con un massimo di 20 px come nell’interfaccia. Sfocatura e rifrazione sono indipendenti. In modalità Trasparente il centro resta nitido. Frecce: sposta il vetro; Maiusc + frecce: passi più grandi.</small>
<img id="scenePhoto" hidden alt="" src=__BACKGROUND__>
<script>
'use strict';
const nativeFragment=__FRAGMENT__;
const canvas=document.getElementById('view'), gl=canvas.getContext('webgl2',{alpha:false,antialias:false,preserveDrawingBuffer:true});
const el=id=>document.getElementById(id);
if(!gl){el('error').textContent='WebGL 2 non è disponibile in questo browser.';throw Error('WebGL2 unavailable');}
function program(fragment){
 const p=gl.createProgram();
 for(const [type,source] of [[gl.VERTEX_SHADER,`#version 300 es
 in vec2 pos;out vec2 v_texcoord;void main(){gl_Position=vec4(pos,0,1);v_texcoord=vec2(pos.x*.5+.5,.5-pos.y*.5);}`],[gl.FRAGMENT_SHADER,fragment]]){
  const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);
  if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));gl.attachShader(p,s);
 }
 gl.linkProgram(p);if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(p));return p;
}
try{
 let glass=program(nativeFragment);const plain=program(`#version 300 es
 precision highp float;uniform sampler2D tex;in vec2 v_texcoord;out vec4 fragColor;void main(){fragColor=texture(tex,v_texcoord);}`);
 const vertices=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,vertices);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
 function use(p){gl.useProgram(p);const a=gl.getAttribLocation(p,'pos');gl.enableVertexAttribArray(a);gl.vertexAttribPointer(a,2,gl.FLOAT,false,0,0);}
 function uniform(p,n,...v){const u=gl.getUniformLocation(p,n);if(u===null)return;if(v.length===2)gl.uniform2f(u,...v);else gl.uniform1f(u,v[0]);}
 const background=document.createElement('canvas');background.width=1100;background.height=540;
 const ctx=background.getContext('2d');
 const frosted=document.createElement('canvas');frosted.width=1100;frosted.height=540;
 const texture=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,texture);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
 function upload(){let image=background;if(el('material').value==='frosted'){const b=frosted.getContext('2d');b.clearRect(0,0,1100,540);b.filter=`blur(${el('blur').value}px)`;b.drawImage(background,0,0);image=frosted;}gl.bindTexture(gl.TEXTURE_2D,texture);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,image);}
 // The plain background is uploaded once; only the cropped glass sample changes material.
 const clearTexture=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,clearTexture);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,background);
 let box={x:125,y:52,w:850,h:280},moving=false,drag=null,animation=0,testing=false,testRadius=52,testRegion=false,testNested=false,testMaxRim=20;
 function render(){
  gl.viewport(0,0,1100,540);use(plain);gl.bindTexture(gl.TEXTURE_2D,clearTexture);gl.uniform1i(gl.getUniformLocation(plain,'tex'),0);gl.drawArrays(gl.TRIANGLE_STRIP,0,4);
  gl.viewport(box.x,540-box.y-box.h,box.w,box.h);use(glass);gl.bindTexture(gl.TEXTURE_2D,texture);gl.uniform1i(gl.getUniformLocation(glass,'tex'),0);gl.uniform1i(gl.getUniformLocation(glass,'useMask'),0);gl.uniform1i(gl.getUniformLocation(glass,'enhanced'),1);gl.uniform1i(gl.getUniformLocation(glass,'regionCount'),0);
  for(const [name,value] of Object.entries({radius:testRadius,roundingPower:2,refractionStrength:+el('strength').value/100,edgeThickness:+el('width').value/100,maxRimWidth:testMaxRim,chromaticAberration:testing?0:.1,fresnelStrength:testing?0:.35,specularStrength:testing?0:.5,glassOpacity:1,lensDistortion:0,brightness:1,contrast:1,saturation:1,vibrancy:0,vibrancyDarkness:0,adaptiveDim:0,adaptiveBoost:0,tintAlpha:0}))uniform(glass,name,value);
  if(testRegion){gl.uniform1i(gl.getUniformLocation(glass,'regionCount'),1);gl.uniform4f(gl.getUniformLocation(glass,'regionRects[0]'),0,0,box.w,box.h);gl.uniform4f(gl.getUniformLocation(glass,'regionRadii[0]'),testRadius,testRadius,testRadius,testRadius);gl.uniform4f(gl.getUniformLocation(glass,'regionFeatures[0]'),0,0,0,0);gl.uniform4f(gl.getUniformLocation(glass,'regionDetails[0]'),0,1,0,0);}
  if(testNested){const i=testNested===2?0:1;gl.uniform1i(gl.getUniformLocation(glass,'regionCount'),i+1);gl.uniform4f(gl.getUniformLocation(glass,`regionRects[${i}]`),8.25,8.25,box.w-16.5,box.h-16.5);gl.uniform4f(gl.getUniformLocation(glass,`regionRadii[${i}]`),16,16,16,16);gl.uniform4f(gl.getUniformLocation(glass,`regionFeatures[${i}]`),0,0,0,0);gl.uniform4f(gl.getUniformLocation(glass,`regionDetails[${i}]`),0,1,8,0);}
  uniform(glass,'fullSize',box.w,box.h);uniform(glass,'origin',box.x,box.y);uniform(glass,'sceneSize',1100,540);uniform(glass,'uvPadding',0,0);gl.drawArrays(gl.TRIANGLE_STRIP,0,4);
  el('widthValue').textContent=`${el('width').value}% · ${Math.round(Math.min(Math.min(box.w,box.h)*el('width').value/100,testMaxRim||Infinity))} px (max 20)`;
  el('strengthValue').textContent=`${el('strength').value}%`;el('blurValue').textContent=`${el('material').value==='clear'?0:el('blur').value} px`;el('blur').disabled=el('material').value==='clear';
 }
 function stop(){moving=false;cancelAnimationFrame(animation);el('motion').textContent='Avvia movimento';el('motion').setAttribute('aria-pressed','false');}
 function update(){upload();render();}
 for(const name of ['material','width','strength','blur'])el(name).addEventListener('input',update);
 canvas.addEventListener('pointerdown',e=>{stop();canvas.focus();canvas.setPointerCapture(e.pointerId);drag={x:e.clientX,y:e.clientY,bx:box.x,by:box.y};});
 canvas.addEventListener('pointermove',e=>{if(!drag)return;const k=1100/canvas.getBoundingClientRect().width;box.x=Math.max(0,Math.min(1100-box.w,drag.bx+(e.clientX-drag.x)*k));box.y=Math.max(0,Math.min(540-box.h,drag.by+(e.clientY-drag.y)*k));render();});
 canvas.addEventListener('pointerup',()=>drag=null);canvas.addEventListener('pointercancel',()=>drag=null);
 canvas.addEventListener('keydown',e=>{if(!e.key.startsWith('Arrow'))return;e.preventDefault();stop();const d=e.shiftKey?20:4;box.x=Math.max(0,Math.min(1100-box.w,box.x+(e.key==='ArrowRight'?d:e.key==='ArrowLeft'?-d:0)));box.y=Math.max(0,Math.min(540-box.h,box.y+(e.key==='ArrowDown'?d:e.key==='ArrowUp'?-d:0)));render();});
 el('motion').onclick=()=>{if(moving){stop();return;}moving=true;el('motion').textContent='Ferma movimento';el('motion').setAttribute('aria-pressed','true');const start=performance.now();function frame(t){if(!moving)return;box.y=105+75*Math.sin((t-start)/1800);render();animation=requestAnimationFrame(frame);}animation=requestAnimationFrame(frame);};
 el('reset').onclick=()=>{stop();box={x:125,y:52,w:850,h:280};el('material').value='clear';el('width').value=7;el('strength').value=135;el('blur').value=6;update();};
 function setPhoto(image){
  const scale=Math.max(1100/image.naturalWidth,540/image.naturalHeight);
  ctx.clearRect(0,0,1100,540);ctx.drawImage(image,(1100-image.naturalWidth*scale)/2,(540-image.naturalHeight*scale)/2,image.naturalWidth*scale,image.naturalHeight*scale);
  gl.bindTexture(gl.TEXTURE_2D,clearTexture);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,background);update();
 }
 el('photo').onchange=async()=>{
  const file=el('photo').files[0];if(!file)return;const url=URL.createObjectURL(file);
  try{const photo=new Image();photo.src=url;await photo.decode();stop();setPhoto(photo);el('error').textContent='';}
  catch(e){el('error').textContent='Impossibile aprire questa immagine.';}
  finally{URL.revokeObjectURL(url);}
 };
 const initialPhoto=el('scenePhoto');
 function ready(){setPhoto(initialPhoto);
 window.glassPreview={gl,render,box};
 if(new URLSearchParams(location.search).has('check')){
  const report={ok:false};testing=true;
  try{
   function assert(v,message){if(!v)throw Error(message);}
   const pixels=()=>{const p=new Uint8Array(1100*540*4);gl.readPixels(0,0,1100,540,gl.RGBA,gl.UNSIGNED_BYTE,p);assert(gl.getError()===gl.NO_ERROR,'OpenGL error');return p;};
   const at=(p,x,y,c=0)=>p[((539-y)*1100+x)*4+c];
   // Red and green encode source coordinates: a horizontal slip cannot hide in the pattern.
   const pattern=document.createElement('canvas');pattern.width=1100;pattern.height=540;
   const pc=pattern.getContext('2d'),data=pc.createImageData(1100,540);
   for(let y=0;y<540;y++)for(let x=0;x<1100;x++){const i=(y*1100+x)*4;data.data[i]=Math.round(x/1099*255);data.data[i+1]=Math.round(y/539*255);data.data[i+2]=((x/12|0)+(y/12|0))%2*255;data.data[i+3]=255;}pc.putImageData(data,0,0);
   gl.bindTexture(gl.TEXTURE_2D,texture);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,pattern);
   gl.bindTexture(gl.TEXTURE_2D,clearTexture);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,pattern);
   render();const first=pixels();
   for(const [x,y] of [[550,190],[480,180],[800,200]])for(let c=0;c<3;c++)assert(Math.abs(at(first,x,y,c)-data.data[(y*1100+x)*4+c])<=2,'Center changed without blur');
   const y=box.y+box.h-5;
   const left=at(first,250,y)/data.data[(y*1100+250)*4],right=at(first,850,y)/data.data[(y*1100+850)*4];
   assert(Math.abs(left-right)<.035,'Straight lower edge bends sideways');
   assert(Math.abs(at(first,550,y,1)-data.data[(y*1100+550)*4+1])>10,'Lower edge does not refract');
   for(let c=0;c<3;c++)assert(at(first,550,500,c)===data.data[(500*1100+550)*4+c],'Background moved outside glass');
   box.y+=55;render();const moved=pixels();
   for(let c=0;c<3;c++)assert(Math.abs(at(moved,550,190,c)-data.data[(190*1100+550)*4+c])<=2,'Moving glass carries a frozen background');
   assert(Math.abs(at(moved,550,y,1)-at(first,550,y,1))>10,'Edge sample did not follow the moved glass');
   el('width').value=2;el('strength').value=0;render();pixels();
   el('material').value='frosted';update();pixels();
   // Decode displacement itself: background detail and bottom-rim shading cannot hide a corner seam.
   const originalGlass=glass;
   glass=program(nativeFragment.replace('float glassA =','float packedWidth = bezelWidthPx * 255.0 / 128.0;\n    color = vec3(floor(packedWidth) / 255.0, fract(packedWidth), 0.5);\n    float glassA ='));
   el('width').value=7;
   for(const regions of [false,true])for(const [w,h,limit,expected] of [[200,100,20,7],[850,420,20,20],[980,720,20,20],[1000,840,40,40]]){
    box={x:10,y:10,w,h};testMaxRim=limit;testRadius=23;testRegion=regions;render();const frame=pixels();
    const actual=(at(frame,box.x+Math.floor(w/2),box.y+20)+at(frame,box.x+Math.floor(w/2),box.y+20,1)/255)*128/255;
    assert(Math.abs(actual-expected)<.01,`Rim width changed with panel size: ${w}x${h}, limit=${limit}, regions=${regions}, actual=${actual}`);
   }
   // Exercise the wide-rim corner math independently of the production width cap.
   testMaxRim=0;
   glass=program(nativeFragment.replace('float glassA =','color = vec3(vec2(0.5) + baseOffset * fullSize / 128.0, 0.5);\n    float glassA ='));
   box={x:125,y:52,w:850,h:420};el('width').value=7;el('strength').value=135;
   for(const regions of [false,true])for(const r of [0,8,16,52]){
    testRadius=r;testRegion=regions;render();const frame=pixels();
    for(const sx of [-1,1])for(const sy of [-1,1]){
     const x=box.x+(sx<0?r+2:box.w-r-3),y=box.y+(sy<0?r+2:box.h-r-3);
     if(r<box.h*.07)for(let c=0;c<2;c++){
      const inward=(at(frame,x,y,c)/255-.5)*128*-(c===0?sx:sy);
      assert(inward>1,`Corner loses inward refraction: radius=${r}, regions=${regions}, corner=${sx},${sy}, axis=${c}`);
     }
     for(let c=0;c<2;c++)assert(Math.abs(at(frame,x+sx,y-sy,c)-at(frame,x-sx,y+sy,c))<=6,`Corner refraction jumps: radius=${r}, regions=${regions}, corner=${sx},${sy}`);
    }
   }
   // A continuous direction can still hide a 45-degree crease in the refraction strength.
   glass=program(nativeFragment.replace('float glassA =','float packedDepth = depth * 255.0 / 128.0;\n    color = vec3(floor(packedDepth) / 255.0, fract(packedDepth), 0.5);\n    float glassA ='));
   const depthAt=(frame,x,y)=>(at(frame,x,y)+at(frame,x,y,1)/255)*128/255;
   for(const regions of [false,true])for(const r of [8,16]){
    testRadius=r;testRegion=regions;render();const frame=pixels();
    for(const sx of [-1,1])for(const sy of [-1,1]){
     const x=box.x+(sx<0?r+2:box.w-r-3),y=box.y+(sy<0?r+2:box.h-r-3);
     const crease=depthAt(frame,x+sx,y-sy)+depthAt(frame,x-sx,y+sy)-2*depthAt(frame,x,y);
     assert(Math.abs(crease)<.8,`Diagonal crease in corner depth: radius=${r}, regions=${regions}, corner=${sx},${sy}, crease=${crease}`);
    }
   }
   glass=originalGlass;testRadius=52;testRegion=false;testMaxRim=20;
   // The child edge must reveal the parent's glass, rather than punch a 1-2px hole through both.
   box={x:125,y:52,w:420,h:280};testRadius=23;testRegion=true;testNested=true;
   gl.bindTexture(gl.TEXTURE_2D,texture);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,pattern);
   gl.activeTexture(gl.TEXTURE2);gl.bindTexture(gl.TEXTURE_2D,texture);gl.activeTexture(gl.TEXTURE0);
   gl.useProgram(glass);gl.uniform1i(gl.getUniformLocation(glass,'frostTex'),2);
   testNested=false;render();const parentFrame=pixels();
   testNested=2;render();const childFrame=pixels();
   testNested=true;render();const combinedFrame=pixels();
   // At this straight fractional edge d=-.25, the child covers .31640625 of the pixel.
   const childAlpha=.31640625,px=box.x+8,py=box.y+140;
   for(let c=0;c<3;c++)assert(Math.abs(at(combinedFrame,px,py,c)-(at(childFrame,px,py,c)+(1-childAlpha)*at(parentFrame,px,py,c)))<=2,'Nested edge lost the parent refraction');
   // Encode total glass coverage: the same shader still computes refraction and material selection.
   const nestedGlass=glass;
   glass=program(nativeFragment.replace('if (hasMask) {\n        // Layers only: composite', 'color = vec3(1.0);\n    if (hasMask) {\n        // Layers only: composite'));
   gl.useProgram(glass);gl.uniform1i(gl.getUniformLocation(glass,'frostTex'),2);
   render();const nested=pixels();let samples=0;
   for(let y=2;y<box.h-2;y++)for(let x=2;x<box.w-2;x++){
    const qx=Math.abs(x+.5-box.w/2)-(box.w/2-24.25),qy=Math.abs(y+.5-box.h/2)-(box.h/2-24.25);
    const d=Math.min(Math.max(qx,qy),0)+Math.hypot(Math.max(qx,0),Math.max(qy,0))-16;
    if(d>-1.5&&d<.5){assert(at(nested,box.x+x,box.y+y)>=254,`Nested glass loses parent coverage at ${x},${y}`);samples++;}
   }
   assert(samples>500,'Nested edge probe missed the antialiased curve');
   glass=nestedGlass;testRegion=false;testNested=false;
   report.ok=true;report.checks=['native GLSL compile','clear center','edge-normal direction','edge displacement','fixed background','moving glass','zero refraction','frosted material','20px rim cap for large panels and scaled outputs; small widgets unchanged','four-corner continuity and inward refraction for windows and cards','rounded optical depth without a diagonal crease','nested material edges retain parent glass coverage'];
   testing=false;gl.bindTexture(gl.TEXTURE_2D,clearTexture);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,background);el('reset').click();
   // Headless Firefox omits WebGL canvases from page screenshots; retain the actual GL pixels in 2D.
   const snapshot=pixels(),image=document.createElement('canvas');image.width=1100;image.height=540;
   const imageCtx=image.getContext('2d'),imageData=imageCtx.createImageData(1100,540);
   for(let row=0;row<540;row++)imageData.data.set(snapshot.subarray((539-row)*4400,(540-row)*4400),row*4400);
   imageCtx.putImageData(imageData,0,0);canvas.replaceWith(image);
  }catch(e){report.error=e.message;el('error').textContent=e.message;}
  fetch('/result',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(report)});
 }
 }
 if(initialPhoto.complete && initialPhoto.naturalWidth)ready();else initialPhoto.onload=ready;
 initialPhoto.onerror=()=>{el('error').textContent='Impossibile caricare lo sfondo.';};
}catch(e){el('error').textContent=e.message;throw e;}
</script></html>'''
Path(sys.argv[2]).write_text(html.replace('__FRAGMENT__', json.dumps(shader, ensure_ascii=False)).replace('__BACKGROUND__', json.dumps(image_url)))
print('Created:', sys.argv[2])
