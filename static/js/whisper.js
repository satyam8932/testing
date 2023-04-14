// Voice Recorder with Duration to Server

let startButton = document.getElementById("startButton");
let stopButton = document.getElementById("stopButton");
let mediaRecorder;
let chunks = [];

function startRecording() {
  navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.start();
    startButton.disabled = true;
    stopButton.disabled = false;

    mediaRecorder.ondataavailable = function (e) {
      chunks.push(e.data);
    };

    mediaRecorder.onstop = function (e) {
      let audioBlob = new Blob(chunks, { type: "audio/ogg; codecs=opus" });
      let audioUrl = URL.createObjectURL(audioBlob);
      const audioPlayer = document.getElementById('audio-player');
      const audioElement = new Audio(audioUrl);
      audioPlayer.src = audioUrl;
      let formData = new FormData();
      formData.append("audio", audioBlob);

      fetch("/upload", {
        method: "POST",
        body: formData,
      })
        .then(function (response) {
          console.log("Audio file uploaded successfully!");
        })
        .catch(function (error) {
          console.error("Error uploading audio file:", error);
        });
      
      // audioPlayer.play()
      const audioContext = new AudioContext();
      const fileReader = new FileReader();
      fileReader.onload = function() {
        audioContext.decodeAudioData(fileReader.result).then(function(decodedData) {
          const duration = decodedData.duration;
          var minutes = duration / 60;
          console.log(minutes)
          var data = {'duration': minutes};
          fetch('/duration', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(data)
        })
        .then(response => response.text())
        .then(response => console.log(response));
          
        });
      };
      fileReader.readAsArrayBuffer(audioBlob);
        // Audio Duration Sending to Server
      
      //   audioPlayer.addEventListener('loadedmetadata', function() {
      //   const duration = audioElement.duration;
      //   // console.log(duration);
      //   var minutes = duration / 60;
      //   // var seconds = duration % 60;
      //   // console.log(minutes)
      //   var data = {'duration': minutes};
      //   fetch('/duration', {
      //     method: 'POST',
      //     headers: {'Content-Type': 'application/json'},
      //     body: JSON.stringify(data)
      //   })
      //   .then(response => response.text())
      //   .then(response => console.log(response));
      // });
      
    };
  });
}

function stopRecording() {
  mediaRecorder.stop();
  startButton.disabled = false;
  stopButton.disabled = true;
}


startButton.addEventListener("click", startRecording);
stopButton.addEventListener("click", stopRecording);


// Audio Player for uploaded audio and duration to server

const audioFile = document.getElementById('audioFile');
const audioFilePlayer = document.getElementById('audio-upload-player')

audioFile.addEventListener('change', function(){
  const file = audioFile.files[0];
  const obj = URL.createObjectURL(file);
  audioFilePlayer.src = obj;
})

audioFilePlayer.addEventListener('loadedmetadata', function() {
  var duration = audioFilePlayer.duration;
  var minutes = duration / 60;
  // var seconds = duration % 60;
  console.log(minutes)
  // var data = {'duration': minutes + ':' + (seconds < 10 ? '0' : '') + seconds};
  var data = {'duration': minutes};
  fetch('/duration', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data)
  })
  .then(response => response.text())
  .then(response => console.log(response));
});

//hello
