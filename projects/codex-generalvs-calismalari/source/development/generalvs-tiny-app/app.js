(function(root,factory){
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  if(root.document)api.mount(root.document,root.localStorage);
})(typeof globalThis!=="undefined"?globalThis:this,function(){
  "use strict";
  const KEY="gunluk-gorevler";
  const tidy=value=>String(value??"").trim();
  function add(tasks,text,id){
    const value=tidy(text);
    if(!value)return tasks;
    return tasks.concat({id:id||Date.now().toString(36)+Math.random().toString(36).slice(2,7),text:value,done:false});
  }
  function toggle(tasks,id){return tasks.map(task=>task.id===id?Object.assign({},task,{done:!task.done}):task)}
  function remove(tasks,id){return tasks.filter(task=>task.id!==id)}
  function counts(tasks){const done=tasks.filter(task=>task.done).length;return{total:tasks.length,done:done,open:tasks.length-done}}
  function read(storage){
    try{
      const value=JSON.parse(storage.getItem(KEY)||"[]");
      return Array.isArray(value)?value.filter(task=>task&&typeof task.id==="string"&&typeof task.text==="string").map(task=>({id:task.id,text:tidy(task.text),done:Boolean(task.done)})).filter(task=>task.text):[];
    }catch(error){return[]}
  }
  function write(storage,tasks){storage.setItem(KEY,JSON.stringify(tasks))}
  function mount(doc,storage){
    let tasks=read(storage);
    const form=doc.querySelector("#task-form"),input=doc.querySelector("#task-input"),list=doc.querySelector("#task-list"),counter=doc.querySelector("#counter"),empty=doc.querySelector("#empty");
    function render(){
      const state=counts(tasks);
      counter.textContent=state.done+" / "+state.total+" tamamlandı";
      empty.hidden=state.total>0;
      list.replaceChildren(...tasks.map(task=>{
        const item=doc.createElement("li");
        item.className="task"+(task.done?" done":"");
        item.dataset.id=task.id;
        const check=doc.createElement("input");
        check.type="checkbox";check.checked=task.done;check.setAttribute("aria-label",task.text+" tamamlandı");
        const text=doc.createElement("span");text.textContent=task.text;
        const del=doc.createElement("button");
        del.type="button";del.className="delete";del.textContent="Sil";del.setAttribute("aria-label",task.text+" görevini sil");
        item.append(check,text,del);
        return item;
      }));
    }
    function commit(next){tasks=next;write(storage,tasks);render()}
    form.addEventListener("submit",event=>{
      event.preventDefault();
      const next=add(tasks,input.value);
      if(next!==tasks){commit(next);input.value="";input.focus()}
    });
    list.addEventListener("change",event=>{
      if(event.target.matches('input[type="checkbox"]'))commit(toggle(tasks,event.target.closest("li").dataset.id));
    });
    list.addEventListener("click",event=>{
      if(event.target.matches(".delete"))commit(remove(tasks,event.target.closest("li").dataset.id));
    });
    render();
  }
  return{KEY:KEY,add:add,toggle:toggle,remove:remove,counts:counts,read:read,write:write,mount:mount};
});
