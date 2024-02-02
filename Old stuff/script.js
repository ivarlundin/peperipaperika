var particle = new Particle();
var token = '573526f765ebc51cfd0e5f5469e1e56b5c17b47d';
var buttonState = 0;

function styleButton(){
    if (buttonState == 1) {
        document.getElementById("trigger").style.backgroundColor = "rgba(234, 255, 234, 0.8)";
        document.getElementById("trigger").style.color = "rgb(77, 176, 15)";
    } else {
        document.getElementById("trigger").style.backgroundColor = "rgba(255, 255, 255, 0.2)";
        document.getElementById("trigger").style.color = "rgb(62, 62, 62)";
    }
}
styleButton();


function turnOn() {
    var fnPr = particle.callFunction({ deviceId: 'e00fce68d41921757c574eb6', name: 'led', argument: 'on', auth: token });
    document.getElementById("trigger").innerHTML = "Turn Off";

    fnPr.then(
      function(data) {
        console.log('Function called succesfully:', data);
        buttonState = 1;
        styleButton();
        
      }, function(err) {
        console.log('An error occurred:', err);
      }); 

    return true;
}

function turnOff() {
    var fnPr = particle.callFunction({ deviceId: 'e00fce68d41921757c574eb6', name: 'led', argument: 'off', auth: token });

    document.getElementById("trigger").innerHTML = "Turn On";
    fnPr.then(
      function(data) {
        console.log('Function called succesfully:', data);
        buttonState = 0;
        styleButton();

      }, function(err) {
        console.log('An error occurred:', err);
      }); 

    return true;
}









let text = "";
let field = document.getElementById("specialText");
let counter = 1;

setTimeout(function() {
    document.getElementById("specialText").style.transition = "all 0.2s ease-in-out";
}, 100);

function eventHandler(event) {
    text += event.key;
    field.innerHTML = text;
    animate();
}
addEventListener('keypress', eventHandler);


function animate() {
    setTimeout(function() {
        //console.log(field.innerHTML);
    
        requestAnimationFrame(animate);
        text = field.innerHTML.slice(1);

        field.innerHTML = text;

        // animating/drawing code goes here

    }, 3000);
}

function remove() {
    // Removing the first character
    field.innerHTML = field.innerHTML.slice(1);

    // Removing the last character
    //string.splice(0, string.length - 1);
}


document.addEventListener('keydown', function (e) {
    if (e.key == "Backspace") {
        //console.log("BACK");
        text = field.innerHTML.slice(0, field.length - 1);
        console.log(text);
        

        field.innerHTML = text;
    }
}, false);

document.getElementById("trigger").addEventListener("click", function(){ 
    console.log("Click");
    if (buttonState == 0) {
        turnOn();
    } else if (buttonState == 1) {
        turnOff();
    }
});