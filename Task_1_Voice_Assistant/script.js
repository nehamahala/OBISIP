let listening=false, recognition=null;
const state=document.getElementById("state"), mic=document.getElementById("mic"), orb=document.getElementById("orb");
const heroTitle=document.getElementById("heroTitle"), heroText=document.getElementById("heroText"), log=document.getElementById("log");

function addMsg(who,text){
  const div=document.createElement("div"); div.className="msg "+(who==="You"?"user":"assistant");
  div.innerHTML=`<b>${who}</b><span></span>`; div.querySelector("span").textContent=text; log.appendChild(div); log.scrollTop=log.scrollHeight;
}
function speak(text){
  if("speechSynthesis" in window){ speechSynthesis.cancel(); const u=new SpeechSynthesisUtterance(text); u.rate=.95; speechSynthesis.speak(u); }
}
async function sendCommand(text){
  addMsg("You",text); state.textContent="THINKING"; heroTitle.textContent="Thinking…"; heroText.textContent="Processing your command.";
  try{
    const r=await fetch("/command",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text})});
    const data=await r.json(); addMsg("Assistant",data.reply); speak(data.reply);
    if(data.open_url) setTimeout(()=>window.open(data.open_url,"_blank"),250);
  }catch(e){addMsg("Assistant","I couldn't reach the Python assistant. Make sure the Flask app is running.");}
  state.textContent="READY"; heroTitle.textContent="I'm ready."; heroText.textContent="Click the microphone and speak naturally.";
}
function runQuick(text){sendCommand(text)}
function toggleListen(){
  if(listening){if(recognition) recognition.stop();return;}
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){addMsg("Assistant","Speech recognition is not supported in this browser. Please use Microsoft Edge or Google Chrome.");return;}
  recognition=new SR(); recognition.lang="en-IN"; recognition.interimResults=false; recognition.maxAlternatives=1;
  recognition.onstart=()=>{listening=true;state.textContent="LISTENING";mic.textContent="⏹ Stop Listening";heroTitle.textContent="Listening…";heroText.textContent="Speak your command.";orb.style.transform="scale(1.12)";}
  recognition.onresult=e=>sendCommand(e.results[0][0].transcript);
  recognition.onerror=e=>{addMsg("Assistant","Microphone error: "+e.error);};
  recognition.onend=()=>{listening=false;state.textContent="READY";mic.textContent="🎙 Start Listening";orb.style.transform="scale(1)";}
  recognition.start();
}
