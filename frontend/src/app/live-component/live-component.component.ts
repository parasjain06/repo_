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
this.WellnessService.analysis(this.webcamImage.imageAsDataUrl).subscribe(data => {
  this.data = data
  console.log("data is : " + JSON.stringify(data))
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