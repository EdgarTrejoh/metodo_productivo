// El reproductor externo se solicita solo al activar el enlace.
document.querySelectorAll('.video-frame[data-video-id]').forEach((frame) => {
  const trigger = frame.querySelector('.video-activate');
  const id = frame.dataset.videoId || '';
  if (!trigger || !/^[A-Za-z0-9_-]{11}$/.test(id)) return;
  trigger.addEventListener('click', (event) => {
    event.preventDefault();
    const player = document.createElement('iframe');
    player.src = `https://www.youtube-nocookie.com/embed/${id}?autoplay=1`;
    player.title = `Video: ${frame.dataset.videoTitle || 'Método Productivo'}`;
    player.loading = 'lazy';
    player.referrerPolicy = 'strict-origin-when-cross-origin';
    player.allow = 'autoplay; encrypted-media; picture-in-picture';
    player.allowFullscreen = true;
    trigger.replaceWith(player);
    player.focus();
  }, { once: true });
});
