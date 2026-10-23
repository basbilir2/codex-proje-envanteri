(function(root){
  'use strict';
  const symbols={'+':'+','-':'−','*':'×','/':'÷'};
  function format(number){
    if(!Number.isFinite(number))throw new Error('Sayı çok büyük');
    return String(Number(number.toPrecision(12)));
  }
  function operate(a,operator,b){
    if(operator==='/'&&b===0)throw new Error('Sıfıra bölünemez');
    let result;
    switch(operator){case '+':result=a+b;break;case '-':result=a-b;break;case '*':result=a*b;break;case '/':result=a/b;break;default:throw new Error('Geçersiz işlem');}
    return format(result);
  }
  class Calculator{
    constructor(){this.clear();}
    clear(){this.value='0';this.left=null;this.operator=null;this.fresh=true;this.error='';this.history='';}
    input(key){
      if(key==='clear'){this.clear();return;}
      if(this.error){if(!/^[0-9.]$/.test(key))return;this.clear();}
      try{
        if(/^[0-9.]$/.test(key)){
          if(this.fresh){this.value='0';this.fresh=false;if(!this.operator)this.history='';}
          if(key==='.'){if(!this.value.includes('.'))this.value+='.';}
          else if(this.value.replace(/[-.]/g,'').length<12)this.value=this.value==='0'?key:this.value==='-0'?'-'+key:this.value+key;
        }else if(key==='backspace'){
          if(this.fresh)return;
          this.value=this.value.slice(0,-1);if(this.value===''||this.value==='-')this.value='0';
        }else if(key==='sign'){
          this.value=format(-Number(this.value));
          // A sign entered after an operator starts a negative right operand.
          if(this.operator&&this.fresh){this.value='-0';this.fresh=false;}
        }else if(key==='percent'){
          this.value=format(Number(this.value)/100);this.fresh=false;
        }else if(Object.hasOwn(symbols,key)){
          if(this.operator&&!this.fresh)this.value=operate(this.left,this.operator,Number(this.value));
          this.left=Number(this.value);this.operator=key;this.fresh=true;
          this.history=this.value.replace('.',',')+' '+symbols[key];
        }else if(key==='='&&this.operator&&!this.fresh){
          this.history=String(this.left).replace('.',',')+' '+symbols[this.operator]+' '+this.value.replace('.',',')+' =';
          this.value=operate(this.left,this.operator,Number(this.value));
          this.operator=null;this.left=null;this.fresh=true;
        }
      }catch(error){this.error=error.message;}
    }
  }
  if(typeof module!=='undefined'&&module.exports)module.exports={Calculator,operate};
  else root.Calculator=Calculator;
})(typeof globalThis!=='undefined'?globalThis:this);
