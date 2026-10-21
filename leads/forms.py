from django import forms

from .models import ContactSubmission


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactSubmission
        fields = ('category', 'message', 'name', 'email')
        widgets = {
            'message': forms.Textarea(attrs={'rows': 6, 'maxlength': 3000}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
            'name': forms.TextInput(attrs={'autocomplete': 'name'}),
        }
        error_messages = {
            'category': {'required': 'Selecciona comentario o solicitud.', 'invalid_choice': 'Selecciona una categoría válida.'},
            'message': {'required': 'Escribe tu mensaje.', 'max_length': 'El mensaje no debe superar 3000 caracteres.'},
            'name': {'required': 'Escribe tu nombre.'},
            'email': {'required': 'Escribe tu correo electrónico.', 'invalid': 'Escribe un correo electrónico válido.'},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['email'].required = True

    def clean_message(self):
        message = self.cleaned_data['message'].strip()
        if not message:
            raise forms.ValidationError('Escribe tu mensaje.')
        return message

    def save(self, commit=True):
        submission = super().save(commit=False)
        submission.reply_requested = submission.category == ContactSubmission.Category.REQUEST
        if commit:
            submission.save()
        return submission
