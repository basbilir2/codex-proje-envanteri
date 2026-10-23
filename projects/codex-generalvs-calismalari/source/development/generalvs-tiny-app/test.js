"use strict";
const assert=require("node:assert/strict");
const app=require("./app.js");
let passed=0;
function test(name,fn){fn();passed++;console.log("✓ "+name)}
function memory(){const data=new Map;return{getItem:key=>data.has(key)?data.get(key):null,setItem:(key,value)=>data.set(key,String(value))}}
const base=[{id:"a",text:"Su iç",done:false},{id:"b",text:"Yürü",done:true}];
test("görev metni kırpılır",()=>assert.deepEqual(app.add([],"  Kitap oku  ","x"),[{id:"x",text:"Kitap oku",done:false}]));
test("boş görev reddedilir",()=>{const tasks=[];assert.equal(app.add(tasks,"   ","x"),tasks)});
test("hedef görev tamamlanır",()=>assert.deepEqual(app.toggle(base,"a").map(x=>x.done),[true,true]));
test("diğer görev değişmez",()=>assert.deepEqual(app.toggle(base,"a")[1],base[1]));
test("görev silinir",()=>assert.deepEqual(app.remove(base,"a"),[base[1]]));
test("sayaç doğru hesaplanır",()=>assert.deepEqual(app.counts(base),{total:2,done:1,open:1}));
test("localStorage turu veriyi korur",()=>{const store=memory();app.write(store,base);assert.deepEqual(app.read(store),base)});
test("bozuk kayıt güvenle boş liste olur",()=>{const store=memory();store.setItem(app.KEY,"{bozuk");assert.deepEqual(app.read(store),[])});
console.log("\n"+passed+"/8 doğrulama geçti.");
