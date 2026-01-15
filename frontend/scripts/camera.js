// Camera access and videoStreaming initially
let videoStream = null;
let isStreaming = null;

//videoStream stores the live camera stream
//isStreaming is a camera flag variable which determines if the camera is ON / OFF


//camera acces is asynchronous, browser needs user permission
async function startCamera() {
    //requesting camera access
    try {
        videoStream = await navigator.mediaDevices.getUserMedia({
            //browser asks if access to camera, if yes then webcam turns on
            // a mediastream object is returned and stored in videostream with the given video resolution
            video: {width: 640, height: 480},
            audio: false
        });

        //shows camera in html video
        const videoElement = document.getElementById('video');
        videoElement.srcObject = videoStream;

        console.log('Camera started successfully');
        return true;
    } catch(error) {
        console.log('Camera access failed: ', error);
        return false;
    }
}

//to stop the camera
function stopCamera() {
    if(videoStream) {
        // prevent errors if never started
        videoStream.getTracks().forEach(track => track.stop())
        //all the video tracks are made null 
        videoStream = null;
        //removes reference and marks streaming OFF
    }
    isStreaming = false;
}

function captureFrame() {
    // get video element
    const video = document.getElementById('video');
    // this is the live video playing on the page
    const canvas = document.createElement('canvas');
    //canvas allows pixel level access
    canvas.width = 640;
    canvas.height = 480;

    //takes current frame from video, paints onto canvas, freezes the exact moment 
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    //convert frame to base64 image format
    //0.8 is the compression quality 

    return canvas.toDataURL('image/jpeg', 0.8).split(',')[1];
}

