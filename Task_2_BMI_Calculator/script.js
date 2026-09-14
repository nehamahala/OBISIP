const form=document.getElementById("form"),result=document.getElementById("result"),error=document.getElementById("error");
form.addEventListener("submit",async e=>{e.preventDefault();result.classList.add("hidden");error.classList.add("hidden");
const weight=Number(document.getElementById("weight").value),height=Number(document.getElementById("height").value);
if(weight<=0||height<=0){error.textContent="Please enter positive values.";error.classList.remove("hidden");return}
try{const r=await fetch("/calculate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({weight,height})}),d=await r.json();
if(!r.ok)throw Error(d.message);document.getElementById("bmi").textContent=d.bmi;document.getElementById("cat").textContent=d.category;result.classList.remove("hidden")}
catch(x){error.textContent=x.message||"Unable to calculate BMI.";error.classList.remove("hidden")}});