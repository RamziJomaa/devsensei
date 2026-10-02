import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { timer, Subscription } from 'rxjs';
import { switchMap, takeWhile } from 'rxjs/operators';
// Assuming marked is installed: npm install marked
import { marked } from 'marked';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  repoUrl: string = '';
  githubToken: string = '';
  
  isLoading: boolean = false;
  isPolling: boolean = false;
  error: string | null = null;
  reportMarkdown: string | null = null;
  renderedHtml: string = '';
  
  private pollingSub?: Subscription;

  constructor(private http: HttpClient) {}

  async onSubmit() {
    if (!this.repoUrl) return;
    
    this.isLoading = true;
    this.error = null;
    this.reportMarkdown = null;

    try {
      // 1. Submit Analysis Async
      const reqBody = {
        repo_url: this.repoUrl,
        github_token: this.githubToken || undefined
      };
      
      this.http.post<any>('/api/v1/analyse', reqBody).subscribe({
        next: (res) => {
          this.startPolling(res.analysis_id);
        },
        error: (err) => {
          this.error = err.error?.detail || 'Failed to submit analysis';
          this.isLoading = false;
        }
      });
    } catch (e) {
      this.error = 'Unexpected error occurred.';
      this.isLoading = false;
    }
  }

  private startPolling(analysisId: string) {
    this.isPolling = true;
    
    // 2. Poll every 3 seconds
    this.pollingSub = timer(0, 3000).pipe(
      switchMap(() => this.http.get<any>(`/api/v1/analysis/${analysisId}/status`)),
      takeWhile(res => res.status !== 'done' && res.status !== 'failed', true)
    ).subscribe({
      next: (res) => {
        if (res.status === 'done') {
          this.fetchReport(analysisId);
        } else if (res.status === 'failed') {
          this.error = 'Analysis failed during LangGraph execution.';
          this.isLoading = false;
          this.isPolling = false;
        }
      },
      error: (err) => {
        this.error = 'Failed to poll status.';
        this.isLoading = false;
        this.isPolling = false;
      }
    });
  }

  private fetchReport(analysisId: string) {
    // 3. Fetch the final markdown report
    this.http.get<any>(`/api/v1/report/${analysisId}`).subscribe({
      next: async (res) => {
        this.reportMarkdown = res.markdown_content;
        this.renderedHtml = await marked.parse(this.reportMarkdown || '');
        this.isLoading = false;
        this.isPolling = false;
      },
      error: (err) => {
        this.error = 'Failed to fetch the final report.';
        this.isLoading = false;
        this.isPolling = false;
      }
    });
  }
}
