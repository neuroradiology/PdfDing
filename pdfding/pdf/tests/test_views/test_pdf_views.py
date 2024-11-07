from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from pdf.forms import AddForm, DescriptionForm, NameForm, TagsForm
from pdf.models import Pdf, Tag
from pdf.views.pdf_views import AddPdfMixin, EditPdfMixin, OverviewMixin, PdfMixin


def set_up(self):
    self.client = Client()
    self.user = User.objects.create_user(username=self.username, password=self.password, email='a@a.com')
    self.client.login(username=self.username, password=self.password)


class TestAddPDFMixin(TestCase):
    def test_get_context_get(self):
        add_pdf_mixin = AddPdfMixin()
        generated_context = add_pdf_mixin.get_context_get(None, None)

        self.assertEqual({'form': AddForm}, generated_context)

    def test_pre_obj_save(self):
        user = User.objects.create_user(username='username', password='password', email='a@a.com')
        pdf = Pdf.objects.create(owner=user.profile, name='pdf')
        adjusted_pdf = AddPdfMixin.pre_obj_save(pdf, None, None)

        self.assertEqual(pdf, adjusted_pdf)

    def test_post_obj_save(self):
        user = User.objects.create_user(username='username', password='password', email='a@a.com')
        pdf = Pdf.objects.create(owner=user.profile, name='pdf')
        AddPdfMixin.post_obj_save(pdf, {'tag_string': 'tag_a tag_2'})

        # get pdf again so changes are reflected
        pdf = user.profile.pdf_set.get(name='pdf')

        tag_names = [tag.name for tag in pdf.tags.all()]
        self.assertEqual(set(tag_names), {'tag_2', 'tag_a'})


class TestOverviewMixin(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        self.user = None
        set_up(self)

        # create some pdfs
        for i in range(1, 15):
            pdf = Pdf.objects.create(owner=self.user.profile, name=f'pdf_{i % 5}_{i}')

            # add a tag to pdf 2, 7
            if i % 5 == 2 and i < 10:
                tag = Tag.objects.create(name=f'tag_{i}', owner=self.user.profile)
                pdf.tags.set([tag])

    def test_filter_objects(self):
        response = self.client.get(f'{reverse('pdf_overview')}?q=pdf_2+%23tag_2')
        Pdf.objects.create(owner=self.user.profile, name='pdf')

        filtered_pdfs = OverviewMixin.filter_objects(response.wsgi_request)

        # pdfs 2, 7 and 12 are starting with 'pdf_2' only the pdf 2 and 7 have a tag
        pdf_names = [pdf.name for pdf in filtered_pdfs]

        self.assertEqual(pdf_names, ['pdf_2_2'])

    def test_get_extra_context(self):
        response = self.client.get(f'{reverse('pdf_overview')}?q=pdf_2+%23tag_2')

        generated_extra_context = OverviewMixin.get_extra_context(response.wsgi_request)
        expected_extra_context = {'raw_search_query': 'pdf_2 #tag_2', 'tag_dict': {'t': ['ag_2', 'ag_7']}}

        self.assertEqual(generated_extra_context, expected_extra_context)


class TestPdfMixin(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        self.user = None
        set_up(self)

    def test_get_object(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')

        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        pdf_retrieved = PdfMixin.get_object(response.wsgi_request, pdf.id)

        self.assertEqual(pdf, pdf_retrieved)


class TestEditPdfMixin(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        self.user = None
        set_up(self)

    def test_get_edit_form_get(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf_name', description='some_description')
        tags = [Tag.objects.create(name=f'tag_{i}', owner=self.user.profile) for i in range(2)]
        pdf.tags.set(tags)

        edit_pdf_mixin_object = EditPdfMixin()

        for field, form_class, field_value in zip(
            ['name', 'description', 'tags'],
            [NameForm, DescriptionForm, TagsForm],
            ['pdf_name', 'some_description', 'tag_0 tag_1'],
        ):
            form = edit_pdf_mixin_object.get_edit_form_get(field, pdf)
            self.assertIsInstance(form, form_class)
            if field == 'tags':
                field = 'tag_string'
            self.assertEqual(form.initial, {field: field_value})

    def test_process_field(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf', description='something')
        tag_1 = Tag.objects.create(name='tag_1', owner=self.user.profile)
        tag_2 = Tag.objects.create(name='tag_2', owner=self.user.profile)

        pdf.tags.set([tag_1, tag_2])

        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        EditPdfMixin.process_field('tags', pdf, response.wsgi_request, {'tag_string': 'tag_1 tag_3'})

        # get pdf again with the changes
        pdf = self.user.profile.pdf_set.get(id=pdf.id)
        tag_names = [tag.name for tag in pdf.tags.all()]

        self.assertEqual(sorted(tag_names), sorted(['tag_1', 'tag_3']))
        # check that tag 2 was deleted
        self.assertFalse(self.user.profile.tag_set.filter(name='tag_2').exists())


class TestViews(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        self.user = None
        set_up(self)

    def test_view_get(self):
        # set color to blue
        profile = self.user.profile
        profile.theme_color = 'Custom'
        profile.custom_theme_color = '#ffb3a5'
        profile.save()

        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')
        self.assertEqual(pdf.views, 0)

        response = self.client.get(reverse('view_pdf', kwargs={'identifier': pdf.id}))

        # check that views increased by one
        pdf = self.user.profile.pdf_set.get(name='pdf')
        self.assertEqual(pdf.views, 1)

        self.assertEqual(response.context['pdf_id'], str(pdf.id))
        self.assertEqual(response.context['theme_color_rgb'], '255 179 165')
        self.assertEqual(response.context['user_view_bool'], True)

    def test_update_page_post(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')

        self.client.post(reverse('update_page'), data={'pdf_id': pdf.id, 'current_page': 10})

        # get pdf again with the changes
        pdf = self.user.profile.pdf_set.get(id=pdf.id)

        self.assertEqual(pdf.current_page, 10)

    def test_current_page_get(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')
        pdf.current_page = 5
        pdf.save()

        response = self.client.get(reverse('current_page', kwargs={'identifier': pdf.id}))

        self.assertEqual(response.json()['current_page'], 5)
