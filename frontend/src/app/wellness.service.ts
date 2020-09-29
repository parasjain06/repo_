import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class WellnessService {
  //65.0.5.137
  apiUrl: string = 'http://127.0.0.1:8092';
  headers = new HttpHeaders().set('Content-Type', 'application/json');

  constructor(private http: HttpClient) { }

  public argument:String = null;

  public record_time :any;//capture time

  analysis(image:String): Observable<any> {
    let API_URL = `${this.apiUrl}/wellness`;
    return this.http.post<any>(API_URL, JSON.stringify(image), { headers: this.headers})
      .pipe(
            catchError(this.error)
      )
  }
  
  error(error: HttpErrorResponse) {
    let errorMessage = '';
    if (error.error instanceof ErrorEvent) {
        errorMessage = error.error.message;
    } else {
            errorMessage = `Error Code: ${error.status}\nMessage: ${error.message}`;
    }
    console.log(errorMessage);
    return throwError(errorMessage);
  }
}
