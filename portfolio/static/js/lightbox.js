document.addEventListener('click', function (e) {
  const target = e.target;
  if (target && (target.classList.contains('project-thumb') || target.classList.contains('gallery-thumb'))) {
    const src = target.getAttribute('data-large') || target.src;
    let modal = document.getElementById('lightbox-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'lightbox-modal';
      modal.innerHTML = `
      <div class="modal-backdrop" style="position:fixed;inset:0;background:rgba(0,0,0,0.6);display:flex;align-items:center;justify-content:center;z-index:1050;">
        <img src="" style="max-width:95%;max-height:90%;box-shadow:0 10px 40px rgba(0,0,0,0.6);border-radius:8px;" />
      </div>`;
      document.body.appendChild(modal);
      modal.addEventListener('click', () => modal.remove());
    }
    const img = modal.querySelector('img');
    img.src = src;
  }
});
