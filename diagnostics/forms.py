import json,re
from importlib.resources import files
from django import forms
QUESTIONS=json.loads(files('diagnostics').joinpath('questions.json').read_text(encoding='utf-8'))
class QuestionForm(forms.Form):
    def __init__(self,*args,number,**kwargs):
        super().__init__(*args,**kwargs)
        q=QUESTIONS[number-1]
        self.fields['answer']=forms.ChoiceField(label=q['question'],choices=q['choices'],widget=forms.RadioSelect,error_messages={'required':'Selecciona una opción para continuar.'})
class CaptureForm(forms.Form):
    name=forms.CharField(label='Nombre de la persona',max_length=150)
    email=forms.EmailField(label='Correo electrónico',max_length=254)
    company=forms.CharField(label='Nombre de la empresa',max_length=180)
    whatsapp=forms.CharField(label='WhatsApp (opcional)',required=False,max_length=20)
    service=forms.BooleanField(label='Acepto el uso de datos sintéticos para esta prueba local. Texto de servicio definitivo pendiente.')
    commercial=forms.BooleanField(label='Quiero recibir contenidos y novedades (opcional; registro de prueba).',required=False)
    def clean_email(self):return self.cleaned_data['email'].strip().lower()
    def clean_whatsapp(self):
        v=self.cleaned_data['whatsapp'].strip()
        if v and not re.fullmatch(r'\+?[0-9 ()-]{7,20}',v):raise forms.ValidationError('Escribe un teléfono con clave de país o deja el campo vacío.')
        return v
