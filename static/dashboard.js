(() => {
  const dialog = document.getElementById('client-dialog');
  const name = document.getElementById('client-name');
  if (!dialog || typeof dialog.showModal !== 'function') return;
  const open = () => {
    if (dialog.open) dialog.close();
    dialog.showModal();
    name.focus();
  };
  document.querySelectorAll('[data-open-client]').forEach(button => {
    button.addEventListener('click', event => { event.preventDefault(); open(); });
  });
  document.querySelectorAll('[data-close-client]').forEach(button => {
    button.addEventListener('click', event => { event.preventDefault(); dialog.close(); });
  });
  dialog.addEventListener('click', event => {
    const bounds = dialog.getBoundingClientRect();
    if (event.target === dialog && (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom)) dialog.close();
  });
  dialog.querySelector('form').addEventListener('submit', event => {
    name.value = name.value.trim();
    if (!name.value) {
      event.preventDefault();
      name.setCustomValidity('Enter a client name.');
      name.reportValidity();
    }
  });
  name.addEventListener('input', () => name.setCustomValidity(''));
  if (dialog.open) open();
})();
