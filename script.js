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