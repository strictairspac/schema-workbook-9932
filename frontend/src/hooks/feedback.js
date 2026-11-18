export function feedback(message,error=false){let el=document.querySelector('#feedback');if(el){el.textContent=message;el.className=error?'feedback error':'feedback';}}
