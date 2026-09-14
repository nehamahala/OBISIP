async function generatePassword(){
  const payload={
    length:Number(document.getElementById("length").value),
    uppercase:document.getElementById("uppercase").checked,
    lowercase:document.getElementById("lowercase").checked,
    numbers:document.getElementById("numbers").checked,
    symbols:document.getElementById("symbols").checked
  };
  const message=document.getElementById("message");
  message.textContent="";
  try{
    const res=await fetch("/generate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
    const data=await res.json();
    if(!res.ok) throw new Error(data.error||"Unable to generate password.");
    document.getElementById("password").textContent=data.password;
    document.getElementById("strength").textContent=`Generated ${data.password.length}-character password`;
  }catch(err){message.textContent=err.message;}
}
async function copyPassword(){
  const value=document.getElementById("password").textContent;
  if(!value || value.startsWith("Click Generate")) return;
  await navigator.clipboard.writeText(value);
  document.getElementById("strength").textContent="Password copied to clipboard.";
}
generatePassword();
