﻿var correct = 0;
var wrong = 0;
let numberMemory;

$(window).keypress(function(e){
  var code = e.which || e.keyCode;
  switch ( code )
  {
    case 97:
      guess('familjeliv');
	  switchPicture();
      break;
    case 98:
      guess('flashback');
      break;
  }
});

function switchPicture() {
	let number = Math.floor(Math.random() * 14)

	if (number == numberMemory || number > 13) {
		number = Math.floor(Math.random() * 13)
	}
	let myStr = 'assets/pictures/' + number + '.jpg';
	console.log(myStr);

	document.getElementById("picture").src = myStr;
}
function setState(state){
	$('.game-state').hide();
	$('.game-state-'+state).show();

	if($( 'div[class^="mdl-layout__obfuscator"]' ).hasClass('is-visible')){
		$( 'div[class^="mdl-layout__obfuscator"]' ).trigger( "click" );
	}
	
	switch(state){
		case 'game':
			startGame();
			break;
	}
}

function guess(answer){	
	if(quiz.current.f.toLowerCase().startsWith(answer)){
		correct++;
		$("#correct").fadeIn(100).fadeOut(100).fadeIn(100).fadeOut(100).fadeIn(100);
		ga('send', 'event', 'familjeliv-eller-flashback', 'guess', 'correct', 10);
	}else{
		wrong++;
		$("#wrong").fadeIn(100).fadeOut(100).fadeIn(100).fadeOut(100).fadeIn(100);
		ga('send', 'event', 'familjeliv-eller-flashback', 'guess', 'wrong', 20);
	}

	updateProgess();
	
	quiz.getNewSentence();
	$('#sentence').text(quiz.current.s);	
	
	$('#load').text('{f: "'+quiz.current.f+'", s: "'+quiz.current.s+'"},');
}

function startGame(){
	wrong = 0;
	correct = 0;
	updateProgess();
	quiz.getNewSentence();
	$('#sentence').text(quiz.current.s);
	//switchPicture();
}

function updateProgess(){
	switchPicture();
	$('#correct').html(correct);
	$('#wrong').html(wrong);
	var percent = 100;
	if((correct+wrong) > 0){
	  percent = correct/(correct+wrong)*100;
	}
	//document.querySelector('#progress').MaterialProgress.setProgress(percent);
}

function reset(){
	startGame();
	window.localStorage.removeItem("quiz-sentences");
}

String.prototype.startsWith = function(needle){
    return(this.indexOf(needle) == 0)
};

setTimeout(function(){ 
	setState('game'); 
}, 0);
