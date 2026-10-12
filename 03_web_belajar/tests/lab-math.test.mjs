// Menguji matematika web belajar terhadap angka acuan workbook P1.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const html=readFileSync(new URL('../Lab_P1_XAUUSD.html',import.meta.url),'utf8');
const src=html.match(/<script id="lab-math">([\s\S]*?)<\/script>/)[1];
const M=new Function('module',src+';return LabMath;')(undefined);
const near=(a,b,e=1e-9)=>assert.ok(Math.abs(a-b)<e,`${a} != ${b}`);

test('label bar 50 sesuai workbook',()=>{
  const t=M.target(2017,.5);
  near(t.sigma,0.0010630483,1e-10);near(t.delta,0.0005315242,1e-10);near(t.q,-0.0004956630,1e-10);
  assert.equal(t.label,'HOLD');assert.equal(M.target(2020,.5).label,'BUY');
});
test('RSI dan MACD sesuai workbook',()=>{
  const I=M.indicators();
  near(I.rsi[14],60,1e-9);near(I.rsi[15],64.577657,1e-6);near(I.rsi[49],61.23487934,1e-7);
  near(I.macd[49]/M.CLOSES[49],0.0011834227,1e-10);near(I.sig[49]/M.CLOSES[49],0.0011542325,1e-10);
});
test('satu langkah Logistik sesuai workbook',()=>{
  const L=M.logistic();near(L.sd,1.707825128,1e-9);near(L.beta[2],0.234216018,1e-9);
  const p=L.prob(3);near(p[0],0.227574947,1e-9);near(p[1],0.320645697,1e-9);near(p[2],0.451779355,1e-9);
});
test('stump SELL iterasi 1: cut -0,5, gain 0,790588235',()=>{
  const r=M.boost(1,1)[0],t=r.trees[0].root;
  assert.equal(t.cut,-.5);near(t.gain,0.790588235,1e-9);near(t.left.w,12/17);near(t.right.w,-0.48);
});
test('pohon HOLD kedalaman 2 memisahkan rentang tengah',()=>{
  const t=M.boost(2,3)[0].trees[1].root;
  assert.equal(t.cut,-.5);assert.equal(t.left.left,undefined);assert.equal(t.right.cut,1.5);
  assert.ok(M.leafOf(t,0).at(-1).w>0);assert.ok(M.leafOf(t,3).at(-1).w<0);assert.equal(M.leafOf(t,-.5)[1].id,'RR');
});
test('iterasi belajar dari p baru dan sampel terjaga',()=>{
  const R=M.boost(2,3);
  assert.ok(Math.abs(R[1].trees[1].root.G-R[0].trees[1].root.G)>1e-5||Math.abs(R[1].trees[1].root.H-R[0].trees[1].root.H)>1e-5);
  for(const r of R)for(const tr of r.trees){const ids=[];(function w(n){if(n.left){assert.ok(n.gain>0);w(n.left);w(n.right);}else{assert.ok(n.H>=.5);ids.push(...n.idx);}})(tr.root);assert.deepEqual(ids.sort(),[0,1,2,3,4,5]);}
  const p=M.softmax(M.predict(R,0,3));near(p.reduce((a,b)=>a+b,0),1,1e-12);assert.ok(p[1]>1/3);
});
test('metrik: selalu HOLD memberi Macro-F1 rendah',()=>{
  const m=M.metrics([[0,90,0],[0,130,0],[0,88,0]]);near(m.macroF1,(2*130/(260+178))/3,1e-12);
});
