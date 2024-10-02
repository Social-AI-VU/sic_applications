'use strict';

const switcher = document.querySelector('.btn');

switcher.addEventListener('click', function() {
    document.body.classList.toggle('light-theme');
    document.body.classList.toggle('dark-theme');

    const className = document.body.className;
    if(className == "light-theme") {
        this.textContent = "Dark";
    } else {
        this.textContent = "Light";
    }

    console.log('current class name: ' + className);

});

// open an exisiting websocket connection
const socket = new WebSocket('ws://192.168.0.142:8080');

// show a log message when a connection is opened
socket.addEventListener('open', () => {
    console.log("we are connected!");
});

// listen to messages coming from the websocket server and change the 'msg' element in the HTML
socket.addEventListener('message', function (event) {
    var div = document.getElementById('msg');
    div.innerHTML = event.data;
});


socket.addEventListener('message', function (event) {
    console.log(event.data);
});

// when a button is clicked, send a message to websocket server
document.getElementById('button').onclick = function() {
    alert("alert");
    socket.send("button was clicked");
};

// socket.onmessage = function(evt) {
//     var data = JSON.parse(evt.data);
//     if( data.channel == 'render_html' ) {
//         mainBody.html(data.msg);
//         updateListeningIcon('ListeningDone');
//         vuLogo();
//         // englishFlag();
//         // activateButtons();
//         // chatBox();
//         // activateSorting();
//     } else if( data.channel == 'text_transcript' ) {
//         updateSpeechText(data.msg);
//     } else if( data.channel == 'action_audio' ) {
//         updateMicrophone(data.msg);
//     }
// };

// socket.onmessage = function(evt) {
//     var data = evt.data;
//     if( data == 'show the vu logo' ) {
//         // mainBody.html(data.msg);
//         // updateListeningIcon('ListeningDone');
//         vuLogo();
//         // englishFlag();
//         // activateButtons();
//         // chatBox();
//         // activateSorting();
//     } else if( data.channel == 'text_transcript' ) {
//         updateSpeechText(data.msg);
//     } else if( data.channel == 'action_audio' ) {
//         updateMicrophone(data.msg);
//     }
// };

// var iconStyle = 'style="height:10vh"';
// function updateListeningIcon(input) {
// 	if( input.startsWith('ListeningStarted') ) {
// 		$('.listening_icon').html('<img src="img/listening.png" '+iconStyle+'>');
// 		updateSpeechText(''); // clear it
// 	} else if( input == 'ListeningDone' ) {
// 		$('.listening_icon').html('<img src="img/not_listening.png" '+iconStyle+'>');
// 	}
// }

// function vuLogo() {
// 	$('.vu_logo').html('<img src="img/vu_logo.png" '+iconStyle+'>');
// }