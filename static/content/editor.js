document.addEventListener('DOMContentLoaded', () => {
  const field = document.getElementById('id_body');
  if (!field || !window.Quill || !window.QuillTableBetter) return;

  Quill.register({ 'modules/table-better': QuillTableBetter }, true);

  const original = document.createElement('div');
  original.innerHTML = field.value;
  const knownAlt = new Map([...original.querySelectorAll('img[src]')].map((img) => [img.getAttribute('src'), img.alt]));
  const workspace = document.createElement('div');
  workspace.className = 'editor-workspace';
  const editor = document.createElement('div');
  editor.id = 'article-visual-editor';
  field.after(workspace);
  workspace.append(editor);
  const quill = new Quill(editor, {
    theme: 'snow',
    placeholder: 'Escribe el artículo aquí…',
    modules: {
      table: false,
      toolbar: [
        [{ header: [2, 3, false] }],
        ['bold', 'italic'],
        [{ list: 'ordered' }, { list: 'bullet' }],
        ['link', 'blockquote', 'align'],
        ['table-better'],
        ['clean'],
      ],
      'table-better': {
        language: 'en_US',
        menus: ['column', 'row', 'table', 'cell', 'delete'],
        toolbarTable: true,
      },
      keyboard: { bindings: QuillTableBetter.keyboardBindings },
    },
  });
  if (field.value) {
    const delta = quill.clipboard.convert({ html: field.value });
    quill.updateContents(delta, Quill.sources.API);
  }
  field.hidden = true;

  const controls = document.createElement('div');
  controls.className = 'editor-media-controls';
  const choose = document.createElement('button');
  choose.type = 'button';
  choose.textContent = 'Insertar imagen de la biblioteca';
  choose.setAttribute('aria-expanded', 'false');
  const add = document.createElement('a');
  add.href = field.dataset.mediaAddUrl;
  add.target = '_blank';
  add.rel = 'noopener';
  add.textContent = 'Agregar imagen a la biblioteca ↗';
  const picker = document.createElement('div');
  picker.className = 'editor-media-picker';
  picker.hidden = true;
  controls.append(choose, add, picker);
  workspace.append(controls);

  choose.addEventListener('click', async () => {
    picker.hidden = !picker.hidden;
    choose.setAttribute('aria-expanded', String(!picker.hidden));
    if (picker.hidden) return;
    picker.replaceChildren();
    const message = document.createElement('p');
    message.textContent = 'Cargando imágenes…';
    picker.append(message);
    try {
      const response = await fetch(field.dataset.mediaLibraryUrl, { credentials: 'same-origin' });
      if (!response.ok) throw new Error('No se pudo consultar la biblioteca.');
      const data = await response.json();
      picker.replaceChildren();
      if (!data.images.length) {
        message.textContent = 'La biblioteca está vacía. Agrega una imagen y vuelve a abrir este selector.';
        picker.append(message);
      }
      data.images.forEach((image) => {
        knownAlt.set(image.url, image.alt);
        const option = document.createElement('button');
        option.type = 'button';
        const thumbnail = document.createElement('img');
        thumbnail.src = image.thumbnail;
        thumbnail.alt = '';
        const label = document.createElement('span');
        label.textContent = `${image.name} — ${image.alt}`;
        option.append(thumbnail, label);
        option.addEventListener('click', () => {
          const position = quill.getSelection(true)?.index ?? quill.getLength();
          quill.insertEmbed(position, 'image', image.url, 'user');
          const inserted = [...quill.root.querySelectorAll('img')].find((item) => item.getAttribute('src') === image.url && !item.alt);
          if (inserted) inserted.alt = image.alt;
          picker.hidden = true;
          choose.setAttribute('aria-expanded', 'false');
          quill.focus();
        });
        picker.append(option);
      });
    } catch (error) {
      message.textContent = error.message;
      picker.replaceChildren(message);
    }
  });

  field.form.addEventListener('submit', () => {
    quill.getModule('table-better').deleteTableTemporary();
    const output = document.createElement('div');
    output.innerHTML = quill.getSemanticHTML();
    const sourceImages = [...quill.root.querySelectorAll('img')];
    [...output.querySelectorAll('img')].forEach((image, index) => {
      const alt = sourceImages[index]?.alt || knownAlt.get(image.getAttribute('src'));
      if (alt) image.alt = alt;
    });
    field.value = output.innerHTML;
  });
});
