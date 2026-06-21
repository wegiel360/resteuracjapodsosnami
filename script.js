function playPitch(url,vol,r1,r2){
  const a=new Audio(url);
  if(vol!=null)a.volume=vol;
  if(r1!=null&&r2!=null)a.playbackRate=r1+Math.random()*(r2-r1);
  a.play().catch(()=>{});
}
function playSfx(n,r1,r2){playPitch('/static/'+n,0.4,r1||.75,r2||1.3)}
function playPop(){playSfx('NoweZamowienie.mp3',.7,1.4)}
function playDing(){playSfx('Gotowe.mp3',.85,1.15)}
function playSlide(){playSfx('Wrealizacji.mp3',.8,1.2)}
function playChime(){playSfx('Gotowe.mp3',.9,1.1)}
function playBeep(){playSfx('NoweZamowienie.mp3',.8,1.2)}
function playCombo(){playSfx('Wrealizacji.mp3',.85,1.15)}
