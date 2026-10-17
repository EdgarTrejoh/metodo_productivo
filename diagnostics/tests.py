import itertools,time,uuid
from datetime import datetime,timezone as tz
from django.test import TestCase,SimpleTestCase,Client,override_settings
from .domain import evaluate,score_answers,catalog
from .forms import QUESTIONS
from .services import finalize,plus_year
from .models import Diagnostic,Orientation
from leads.models import Lead,Consent
from analytics.models import ProductEvent

class DomainTests(SimpleTestCase):
    def test_utf8_content(self):
        self.assertTrue(QUESTIONS[0]['question'].startswith('\u00bfCuenta con informaci\u00f3n'))
        self.assertTrue(catalog()['actions'][0]['action'].startswith('Re\u00fane los registros'))
    def test_all_6561(self):
        for scores in itertools.product(range(3),repeat=8):
            r=evaluate(scores);self.assertEqual(r['raw_score'],sum(scores))
            self.assertEqual(len(set(a['id'] for a in r['actions'])),3)
            for a in r['actions']:
                self.assertEqual(a['response_score'],scores[a['dimension_id']-1])
                if min(scores)<2:self.assertLess(a['response_score'],2)
            self.assertTrue(all(scores[d-1]==2 for d in r['strengths']))
            self.assertTrue(all(scores[d-1]<2 for d in r['gaps']))
            self.assertEqual(r,evaluate(scores))
    def test_boundaries(self):
        for raw,score,level in [(0,0,'Baja visibilidad'),(6,38,'Baja visibilidad'),(7,44,'Gestión en desarrollo'),(11,69,'Gestión en desarrollo'),(12,75,'Gestión controlada'),(16,100,'Gestión controlada')]:
            r=evaluate([min(2,max(raw-i*2,0)) for i in range(8)])
            self.assertEqual((r['score'],r['level']),(score,level))
    def test_catalog_examples(self):
        for e in catalog()['examples']:self.assertEqual([a['id'] for a in evaluate(e['scores'])['actions']],e['selected_action_ids'])
    def test_invalid(self):
        for v in [[],[2]*7,[2]*9,[True]*8,[1.0]*8,[-1]*8,[3]*8,['2']*8]:
            with self.assertRaises(ValueError):evaluate(v)
    def test_financing(self):
        for opt,val in [('a',2),('b',2),('c',1),('d',0),('e',2)]:self.assertEqual(score_answers([0]*7+[opt])['scores'][7],val)
        with self.assertRaises(ValueError):score_answers([0]*7+['z'])
    def test_no_fake_findings(self):
        self.assertEqual(evaluate([0]*8)['strengths'],[])
        self.assertEqual(evaluate([2]*8)['gaps'],[])
        self.assertEqual(evaluate([0]*7+[2])['strengths'],[8])
    def test_retention_calendar(self):
        self.assertEqual(plus_year(datetime(2024,2,29,tzinfo=tz.utc)),datetime(2025,2,28,tzinfo=tz.utc))
        self.assertEqual(plus_year(datetime(2026,10,16,tzinfo=tz.utc)),datetime(2027,10,16,tzinfo=tz.utc))

DATA={'name':'Persona Ficticia','email':'prueba@example.com','company':'Empresa Demo','whatsapp':'','service':True,'commercial':False}
class PersistenceTests(TestCase):
    def test_idempotent(self):
        execution=uuid.uuid4();a=finalize(execution,[2]*7+['e'],DATA);b=finalize(execution,[0]*7+['d'],dict(DATA,company='Otra'))
        self.assertEqual(a.pk,b.pk);self.assertEqual(Diagnostic.objects.count(),1)
        self.assertEqual(b.result['score'],100);self.assertEqual(b.contact['company'],'Empresa Demo')
        self.assertEqual(Consent.objects.count(),2)
        self.assertEqual(ProductEvent.objects.filter(kind='DIAGNOSIS_RELEASED').count(),1)
    def test_unique_lead_snapshots(self):
        a=finalize(uuid.uuid4(),[2]*7+['e'],DATA)
        finalize(uuid.uuid4(),[0]*7+['d'],dict(DATA,company='Segunda Empresa'))
        a.refresh_from_db();self.assertEqual(a.contact['company'],'Empresa Demo')
        self.assertEqual(Lead.objects.count(),1);self.assertEqual(Diagnostic.objects.count(),2)
        self.assertEqual(ProductEvent.objects.filter(kind='LEAD_CREATED').count(),1)
        self.assertEqual(ProductEvent.objects.filter(kind='CHECK_CONTACT_SUBMITTED').count(),2)
    def test_separate_consents(self):
        d=finalize(uuid.uuid4(),[2]*7+['e'],DATA)
        self.assertTrue(Consent.objects.get(execution=d.execution,purpose='service').granted)
        self.assertFalse(Consent.objects.get(execution=d.execution,purpose='commercial').granted)

class FlowTests(TestCase):
    def questions(self):
        self.client.post('/check-pyme/iniciar/')
        for n in range(1,9):self.client.post(f'/check-pyme/pregunta/{n}/',{'answer':'e' if n==8 else '2'})
    def complete(self):
        self.questions();self.client.post('/check-pyme/datos/',DATA)
    def test_no_preselection(self):
        self.client.post('/check-pyme/iniciar/');r=self.client.get('/check-pyme/pregunta/1/')
        self.assertNotContains(r,'checked');self.assertContains(r,'type="radio"',count=3)
        self.assertEqual(r['Referrer-Policy'],'same-origin')
    def test_no_skipping(self):
        self.client.post('/check-pyme/iniciar/')
        self.assertRedirects(self.client.get('/check-pyme/datos/'),'/check-pyme/pregunta/1/')
        self.assertContains(self.client.post('/check-pyme/pregunta/1/',{}),'Selecciona una opción para continuar.')
        self.assertEqual(Diagnostic.objects.count(),0)
    def test_score_hidden(self):
        self.questions();r=self.client.get('/check-pyme/datos/')
        self.assertContains(r,'Tu informe está listo');self.assertNotContains(r,'Gestión controlada');self.assertNotContains(r,'100 / 100')
    def test_required_contact(self):
        self.questions();self.client.post('/check-pyme/datos/',{'email':'invalido'})
        self.assertEqual(Diagnostic.objects.count(),0)
    def test_optional_whatsapp_normalized_email(self):
        self.questions();self.client.post('/check-pyme/datos/',dict(DATA,email='PRUEBA@EXAMPLE.COM'))
        self.assertEqual(Lead.objects.get().email,'prueba@example.com');self.assertEqual(Diagnostic.objects.get().contact['whatsapp'],'')
    def test_result_nostore(self):
        self.complete();r=self.client.get('/check-pyme/resultado/')
        self.assertContains(r,'100 / 100');self.assertIn('no-store',r['Cache-Control'])
    def test_pdf_retries(self):
        self.complete()
        for _ in range(2):
            r=self.client.get('/check-pyme/informe.pdf');self.assertEqual(r['Content-Type'],'application/pdf');self.assertTrue(r.content.startswith(b'%PDF'))
        self.assertEqual(Diagnostic.objects.count(),1);self.assertFalse(ProductEvent.objects.filter(kind='PDF_DOWNLOADED').exists())
    def test_orientation(self):
        self.complete();self.client.post('/check-pyme/orientacion/');self.client.post('/check-pyme/orientacion/')
        self.assertEqual(Orientation.objects.count(),1);self.assertEqual(ProductEvent.objects.filter(kind='ORIENTATION_REQUESTED').count(),1)
    def test_exit_revokes(self):
        self.complete();self.client.post('/check-pyme/salir/')
        for url in ['/check-pyme/resultado/','/check-pyme/informe.pdf']:self.assertEqual(self.client.get(url).status_code,410)
        self.assertEqual(Diagnostic.objects.count(),1)
    def test_navigation_revokes(self):
        self.complete();self.client.get('/');self.assertEqual(self.client.get('/check-pyme/resultado/').status_code,410)
    def test_different_browser(self):
        self.complete();self.assertEqual(Client().get('/check-pyme/resultado/').status_code,410)
    def test_no_recovery(self):
        self.complete();d=Diagnostic.objects.get()
        self.assertEqual(self.client.get('/diagnostico/'+str(d.pk)+'/').status_code,404)
        self.assertEqual(self.client.get('/recuperar-diagnostico/').status_code,404)
    @override_settings(CHECK_CONTEXT_TTL_SECONDS=60)
    def test_expiry(self):
        self.complete();s=self.client.session;ctx=s['check'];ctx['started']=time.time()-61;s['check']=ctx;s.save()
        self.assertEqual(self.client.get('/check-pyme/resultado/').status_code,410)
    def test_new_run(self):
        self.complete();self.client.post('/check-pyme/salir/');self.complete()
        self.assertEqual(Diagnostic.objects.count(),2);self.assertEqual(Lead.objects.count(),1)
    def test_post_required(self):
        for url in ['/check-pyme/iniciar/','/check-pyme/orientacion/','/check-pyme/salir/']:self.assertEqual(self.client.get(url).status_code,405)
    def test_csrf(self):self.assertEqual(Client(enforce_csrf_checks=True).post('/check-pyme/iniciar/').status_code,403)
    def test_admin_otp(self):
        from django.contrib.auth.models import User
        user=User.objects.create_superuser('demo','admin@example.com','test-password-only');self.client.force_login(user)
        r=self.client.get('/backoffice/');self.assertEqual(r.status_code,302);self.assertIn('/login/',r.url)
