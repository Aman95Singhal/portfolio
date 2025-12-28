document.addEventListener('DOMContentLoaded', function() {
  const fileInput = document.getElementById('upload-file');
  const preview = document.getElementById('upload-preview');
  const progressWrap = document.getElementById('upload-progress');
  const progressBar = document.getElementById('upload-progress-bar');
  const form = document.getElementById('upload-form');

  if (fileInput) {
    fileInput.addEventListener('change', function() {
      const f = this.files && this.files[0];
      if (!f) return;
      const r = new FileReader();
      r.onload = function(ev) {
        preview.src = ev.target.result;
        preview.style.display = 'block';
      };
      r.readAsDataURL(f);
    });
  }

  if (form) {
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      const fd = new FormData(form);
      const xhr = new XMLHttpRequest();
      progressWrap.style.display = 'block';
      xhr.upload.onprogress = function(ev) {
        if (ev.lengthComputable) {
          const pct = Math.round((ev.loaded / ev.total) * 100);
          progressBar.style.width = pct + '%';
        }
      };
      xhr.onload = function() {
        if (xhr.status >= 200 && xhr.status < 400) {
          // reload to show new uploads
          window.location.reload();
        } else {
          alert('Upload failed');
        }
      };
      xhr.open('POST', form.action, true);
      xhr.send(fd);
    });
  }

  // SSE for leads
  if (window.EventSource) {
    try {
      const es = new EventSource('/admin/lead_stream');
      es.onmessage = function(e) {
        try {
          const data = JSON.parse(e.data);
          const countEl = document.getElementById('lead-count');
          if (countEl) {
            const current = parseInt(countEl.textContent || '0', 10) || 0;
            countEl.textContent = current + 1;
          }
          // Bootstrap toast (if available)
          if (window.bootstrap) {
            const toastHtml = `<div class="toast align-items-center text-bg-primary border-0" role="alert" aria-live="assertive" aria-atomic="true">`+
                              `<div class="d-flex"><div class="toast-body">New lead from ${data.name} &lt;${data.email}&gt;</div>`+
                              `<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button></div></div>`;
            const container = document.createElement('div');
            container.innerHTML = toastHtml;
            document.body.appendChild(container);
            const toastEl = container.querySelector('.toast');
            const toast = new bootstrap.Toast(toastEl);
            toast.show();
            // cleanup after hide
            toastEl.addEventListener('hidden.bs.toast', () => container.remove());
          }
        } catch (err) {
          console.error('Lead parse error', err);
        }
      };
    } catch (err) {
      console.error('EventSource error', err);
    }
  }
});
