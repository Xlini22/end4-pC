#!/usr/bin/env python3
"""CPU-only regression: media moves without zoom; icons keep their reference curve."""
from pathlib import Path
import re
import subprocess

repo = Path(__file__).resolve().parents[1]
media = (repo / 'modules/ii/dock/DockMedia.qml').read_text()
engine = (repo / 'modules/common/DockMagnify.qml').read_text()
assert 'Component.onCompleted: root.magnifyId = DockMagnify.register(root, false)' in media
assert 'Component.onDestruction: DockMagnify.unregister(root.magnifyId)' in media
shift = re.search(r'transform: Translate \{\s*x: ([^\n]+)', media)[1]
hover = re.search(r'onHoveredChanged: \{([\s\S]*?)\n        \}', media)[1]
assert 'enabled: DockStyle.magnifying' in media
assert not re.search(r'^    scale:', media)
functions = '\n'.join(re.search(r'    function ' + name + r'\([\s\S]*?\n    \}', engine)[0]
                      for name in ['register', 'unregister', 'clear', 'recompute'])
subprocess.run(['node', '-e', r'''
const assert=require('node:assert/strict');
const DockStyle={magnifying:true,magnification:1.6};
const window={};
const root={entries:[],nextId:0,values:{},amplitude:1,pointer:0,window,influenceDistance:110,nudge:19.2};
FUNCTIONS
root.clear=clear;
const parent={mapToItem:(ignored,x,y)=>({x,y})};
const items=[{x:0,width:40},{x:240,width:40},{x:290,width:40},{x:340,width:40},{x:390,width:40}]
 .map(item=>({...item,visible:true,parent,QsWindow:{window}}));
const ids=items.map(register);
const music={x:50,width:180,visible:true,parent,QsWindow:{window}};
const musicId=register(music,false);
for(const amplitude of [.2,.6,1])for(const pointer of [-200,20,100,140,180,260,500]){
 root.amplitude=amplitude;root.pointer=pointer;recompute();
 items.forEach((item,i)=>{
  const distance=pointer-item.x-item.width/2;
  const fraction=Math.min(1,Math.abs(distance)/root.influenceDistance);
  const scale=1+(DockStyle.magnification-1)*amplitude*(1-fraction);
  const shift=-Math.sign(distance)*root.nudge*amplitude*(fraction<1?fraction*scale:1);
  assert.equal(root.values[ids[i]].scale,scale);assert.equal(root.values[ids[i]].shift,shift);
 });
 assert.equal(root.values[musicId].scale,1);
 const left=root.values[ids[0]],right=root.values[ids[1]];
 const from=left.shift+(left.scale-1)*20,to=right.shift-(right.scale-1)*20;
 const fraction=Math.max(0,Math.min(1,(pointer-music.x)/music.width));
 assert.equal(root.values[musicId].shift,from+(to-from)*fraction);
}
// Moving between distant apps must leave the intervening icons AND card stationary.
root.amplitude=1;
for(const pointer of [380,400,420,440,480,540]){
 root.pointer=pointer;recompute();
 assert.equal(root.values[ids[1]].shift,-root.nudge);
 assert.equal(root.values[musicId].shift,-root.nudge);
}
// No discontinuity when entering or leaving either end of the media card.
for(const edge of [music.x,music.x+music.width]){
 root.pointer=edge-.001;recompute();const before=root.values[musicId].shift;
 root.pointer=edge+.001;recompute();assert.ok(Math.abs(root.values[musicId].shift-before)<.01);
}
root.amplitude=0;recompute();assert.deepEqual(root.values,{});
root.amplitude=1;DockStyle.magnifying=false;recompute();assert.deepEqual(root.values,{});
unregister(ids[0]);assert.ok(!root.entries.some(entry=>entry.id===ids[0]));
// Capture the entry-side position once and retain it throughout the card hover.
const readShift=new Function('root','magnifyHover','return '+process.argv[1]);
const hoverChanged=new Function('root','hovered',process.argv[2]);
const card={magnifyHoverShift:0,magnifyValue:{shift:0}},pointer={hovered:false};
for(const entryShift of [-18,18]){
 card.magnifyValue={shift:entryShift};pointer.hovered=true;hoverChanged(card,true);
 for(const next of [-20,-10,0,10,20]){
  card.magnifyValue={shift:next};assert.equal(readShift(card,pointer),entryShift);
 }
 pointer.hovered=false;hoverChanged(card,false);
 assert.equal(readShift(card,pointer),20);
}
card.magnifyValue=null;assert.equal(readShift(card,pointer),0);
'''.replace('FUNCTIONS', functions), shift, hover], check=True)
print('dock media: OK (entry-side position held during hover, adjacent-edge movement and original icon curve)')
