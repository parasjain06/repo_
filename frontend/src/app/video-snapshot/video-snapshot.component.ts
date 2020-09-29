import { Component, ViewChild, ElementRef, Input, OnInit } from '@angular/core';
import {WellnessService } from '../wellness.service'
@Component({
selector: 'app-video-snapshot',
templateUrl: './video-snapshot.component.html',
styleUrls: ['./video-snapshot.component.css']
})
export class VideoSnapshotComponent implements OnInit{
@ViewChild('videoElement') public videoElement: ElementRef;
@Input('snapshotName') public snapshotName: string;
@Input('downloadImageType') public userImageType: string;
public videoUrl: any;
public videoLoaded = false;
public loadingState = false;
public imageTypes = ['JPG', 'PNG', 'BMP', 'TIFF', 'GIF', 'PPM', 'PGM', 'PBM', 'PNM', 'WebP', 'HEIF', 'BPG', 'ECW', 'FITS', 'FLIP', 'PAM', 'CD5', 'CPT', 'PSD', 'PSP', 'XCF', 'PDN'];
public data:any;
public id:any;
public video:any;
public responseData:any;
public videoPlaying:boolean=false;
public image:any;
ngOnInit(): void {
console.log(this.videoLoaded)
this.id = setInterval(this.clickPicture, 5000);
}
constructor(public WellnessService : WellnessService) { }
public readUrl(event) {
console.log(this.videoLoaded)
this.loadingState = true;
this.videoLoaded = false;
if (event.target.files && event.target.files[0]) {
const reader = new FileReader();
reader.onload = (data: any) => {
this.playVideo(data.target.result);
};
reader.readAsDataURL(event.target.files[0]);
}
}

public clickPicture(){
document.getElementById("clickPicture").click();
if(this.videoLoaded){
setTimeout (() => {
this.triggerSnapshot();
}, 1000);
}
}

public triggerSnapshot() {
let canvasElement = document.getElementById('canvas') as HTMLCanvasElement;
const video = this.videoElement.nativeElement;
const context = canvasElement.getContext('2d');
canvasElement.width = 500;
canvasElement.height = 400;
context.fillRect(0, 0, 500, 400);
context.drawImage(video, 0, 0, 500, 400);
const link = document.createElement('a');
this.snapshotName = this.snapshotName !== '' ? this.snapshotName : 'snapshot';
this.userImageType = 'JPG';
link.setAttribute('download', this.snapshotName + '.' + this.userImageType);
const dataURL = canvasElement.toDataURL('image/jpeg');
this.image = (dataURL)
console.log("dataURL "+JSON.stringify(dataURL));
this.processData();
}



public processData(): void {
let eAnalyse = document.getElementById("ALL") 
if(eAnalyse !=null){
eAnalyse.click();
}
}


public all(){
  console.log("value of image is :" +this.image)
  console.log("value of Json stringify image is :" +JSON.stringify(this.image))
console.log("all");
this.WellnessService.analysis(this.image).subscribe(data => {
this.responseData = data
console.log("response data is " + JSON.stringify(this.responseData))
})
}


public playVideo(url) {
this.loadingState = false;
this.videoLoaded = true;
this.videoUrl = url;
if (this.videoElement !== undefined) {
this.videoElement.nativeElement.load();
}
} 

}