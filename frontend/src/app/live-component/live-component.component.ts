import { Component, OnDestroy, OnInit } from '@angular/core';
import {Subject,Observable,forkJoin, of } from 'rxjs';
import {WebcamImage, WebcamInitError} from 'ngx-webcam';
import { catchError } from 'rxjs/operators';
import {WellnessService } from '../wellness.service'
@Component({
selector: 'app-live-component',
templateUrl: './live-component.component.html',
styleUrls: ['./live-component.component.css']
})
export class LiveComponentComponent implements OnInit {
public webcamImage: WebcamImage = null;
public showWebcam = true;
public errors: WebcamInitError[] = [];
public name : string;

//to display Recommendations counters are used
public posCount = 0
public drowCount = 0

//duration of badPosture and drowsiness
public badPosDrtn = 0
public drowsinessDrtn = 0 
public totalDuration = 0
public drowsinessCount = 0
public wrongPosFrameCount = 0
public totalFrameCount = 0

// webcam snapshot trigger
private trigger: Subject<void> = new Subject<void>();
id:any; //to clearup set interval looping
public data:any;
constructor(public WellnessService : WellnessService) { }

public ngOnInit(): void {
this.id = setInterval(this.triggerSnapshot, 5000);
}
public triggerSnapshot(): void {
document.getElementById("clickPicture").click();
this.trigger.next();
setTimeout (() => {
this.processData();
}, 1000);
}
public processData(): void {
let eAnalyse = document.getElementById("ALL") 
if(eAnalyse !=null){
eAnalyse.click();
}
}
public all(){
console.log("image value is" + (this.webcamImage.imageAsDataUrl))
console.log("all");

if (this.drowCount ==7)
  {
    this.drowCount=0
  }
  if (this.posCount ==7)
  {
    this.posCount = 0
  }

this.WellnessService.analysis(this.webcamImage.imageAsDataUrl).subscribe(data => {
  this.data = data
  console.log("data is : " + JSON.stringify(data))
  if(data.drowText == "YES")
  {
    this.drowCount= this.drowCount+1
    this.drowsinessCount= this.drowsinessCount+1
  }
  if (data.correctPos == "NO")
  {
    this.posCount =this.posCount +1
  }
  this.wrongPosFrameCount = data.wrongPosFrame
  this.totalFrameCount = data.totalFrames
  
})

//wrongPosFrameCount
//calculate the time 
this.badPosDrtn = Number(((this.wrongPosFrameCount * 4)/60 ).toFixed(2))
this.drowsinessDrtn = Number(((this.drowsinessCount * 4)/60).toFixed(2))
this.totalDuration=Number(((this.totalFrameCount * 4)/60).toFixed(2))
}


public Notify()
{
  console.log("inside notify")
  clearInterval(this.id)
  this.WellnessService.notify(this.webcamImage.imageAsDataUrl).subscribe(data => {

  })
  
}

public handleInitError(error: WebcamInitError): void {
this.errors.push(error);
}
public handleImage(webcamImage: WebcamImage): void {
this.webcamImage = webcamImage;
}
public get triggerObservable(): Observable<void> {
return this.trigger.asObservable();
}

public ngOnDestroy(){
clearInterval(this.id)
}
/*public webCam : boolean = true;
public id : any;
public data:any;
ngOnInit(): void {
let video = document.getElementById('video') as HTMLVideoElement;
if(this.webCam){
if(navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
navigator.mediaDevices.getUserMedia({ video: true }).then(function(stream) {
video.srcObject = stream;
video.play();
});
}
}

this.id = setInterval(this.snap, 5000);
}
public snap():any{
let canvas = document.getElementById('canvas') as HTMLCanvasElement;
let context = canvas.getContext('2d');
let video = document.getElementById('video') as HTMLVideoElement;
let image = context.drawImage(video, 0, 0, 500, 400);
this.image = canvas.toDataURL();
console.log("image "+canvas.toDataURL());
this.WellnessService.analysis(this.image ).subscribe(data => {
// this.data = data;
console.log("data===="+JSON.stringify(data));
})
}*/
}