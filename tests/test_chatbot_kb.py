import unittest

from chatbot_kb import get_kb_answer


class TestChatbotKB(unittest.TestCase):
    def test_specificity_proposal_manager(self):
        res = get_kb_answer('proposal manager rush schedule')
        self.assertEqual(res['source'], 'role_proposal_manager')

    def test_intent_longer_first(self):
        # Ensure 'proposal manager' wins over generic 'proposal'
        res = get_kb_answer('need proposal manager guidance for color review')
        self.assertEqual(res['source'], 'role_proposal_manager')

    def test_role_direct_tag(self):
        res = get_kb_answer('economist analysis for pricing')
        self.assertEqual(res['source'], 'role_economist')

    def test_navigation_templates(self):
        res = get_kb_answer('where do I find templates')
        self.assertIn(res['source'], {'proposal_templates', 'navigation_help'})

    def test_pricing_calculator_help(self):
        res = get_kb_answer('use pricing calculator and profit margin')
        self.assertEqual(res['source'], 'pricing_calculator_help')

    def test_fallback(self):
        res = get_kb_answer('zzzxxyy unknown topic 12345')
        self.assertEqual(res['source'], 'fallback')


if __name__ == '__main__':
    unittest.main()
