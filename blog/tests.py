from django.test import TestCase, Client
from django.urls import reverse
import json


class PirateTranslationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('blog:translate_pirate')

    def test_valid_translation_request(self):
        response = self.client.post(
            self.url,
            json.dumps({'text': 'Hello world'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('translated', response.json())

    def test_missing_text_field(self):
        response = self.client.post(
            self.url,
            json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'No text provided')

    def test_invalid_json_format(self):
        response = self.client.post(
            self.url,
            'Not a JSON',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'Invalid request format')