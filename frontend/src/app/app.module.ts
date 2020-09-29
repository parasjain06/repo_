import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { LiveComponentComponent } from './live-component/live-component.component';
import { HttpClientModule } from '@angular/common/http';
import { VideoSnapshotComponent } from './video-snapshot/video-snapshot.component';
import {WebcamModule} from 'ngx-webcam';
@NgModule({
  declarations: [
    AppComponent,
    LiveComponentComponent,
    VideoSnapshotComponent
  ],
  imports: [
    HttpClientModule,
    BrowserModule,
    AppRoutingModule,
    WebcamModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
