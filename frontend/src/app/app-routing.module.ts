import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { LiveComponentComponent} from './live-component/live-component.component';
import { VideoSnapshotComponent} from './video-snapshot/video-snapshot.component'
const routes: Routes = [
  {path :"", component : LiveComponentComponent  },
  {path :"recorded", component : VideoSnapshotComponent}
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
