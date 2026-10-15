import copy
import unittest

from strip_sponsors import replace, strip_json, strip_palette, strip_sidebar


class SponsorTransformTests(unittest.TestCase):
    def test_sidebar_supports_both_original_and_upstream_removed_ad_slots(self):
        shared = """  CrownOutlined,
  HeartOutlined,
const DONATE_URL = 'https://donate.sanaei.dev/';
  | 'sponsors'
  sponsors: CrownOutlined,
function DonateButton({ ariaLabel }: { ariaLabel: string }) {
  return <a href={DONATE_URL}><HeartOutlined /></a>;
}

function DocsButton() { return <a href="https://docs.sanaei.dev/">Docs</a>; }
      { key: '/sponsors', icon: 'sponsors', title: t('menu.sponsors') },
              <DonateButton ariaLabel={t('menu.donate') || 'Donate'} />
            <DonateButton ariaLabel={t('menu.donate') || 'Donate'} />
"""
        for slots in ("", "import SponsorSlot from '@/components/sponsor/SponsorSlot';\n  <SponsorSlot slot=\"sidebar\" />\n  <SponsorSlot slot=\"sidebar\" />\n"):
            cleaned = strip_sidebar(slots + shared)
            self.assertNotIn('Sponsor', cleaned)
            self.assertNotIn('Donate', cleaned)
            self.assertIn('https://docs.sanaei.dev/', cleaned)

    def test_translation_updates_preserve_new_protocol_and_user_ad_tag_settings(self):
        original = {
            'menu': {'sponsors': 'Sponsors', 'donate': 'Donate', 'hosts': 'Hosts'},
            'pages': {'sponsors': {'newPlacement': 'Changed ad'}, 'inbounds': {
                'mtgPendingHandshakesMaxPerIp': 'New upstream setting', 'mtgAdTagInvalid': 'Protocol validation'}},
        }
        expected = copy.deepcopy(original)
        del expected['menu']['sponsors']
        del expected['menu']['donate']
        del expected['pages']['sponsors']
        self.assertEqual(strip_json(original, 'translation'), expected)

    def test_openapi_keeps_unrelated_protocol_schemas_and_endpoints(self):
        data = {'paths': {'/sponsors': {}, '/inbounds': {'get': {}}},
                'components': {'schemas': {'panel.SponsorList': {}, 'panel.Sponsor': {}, 'MTProto': {'adTag': {}}}}}
        self.assertEqual(strip_json(data, 'openapi'), {
            'paths': {'/inbounds': {'get': {}}}, 'components': {'schemas': {'MTProto': {'adTag': {}}}}})

    def test_command_palette_keeps_neighboring_navigation(self):
        text = "  CrownOutlined,\nconst pages = [\n      {\n        path: '/sponsors',\n        title: t('menu.sponsors'),\n        icon: <CrownOutlined />,\n      },\n      { path: '/inbounds' },\n];\n"
        self.assertEqual(strip_palette(text), "const pages = [\n      { path: '/inbounds' },\n];\n")

    def test_unknown_shared_code_structure_stops_instead_of_deleting_more(self):
        with self.assertRaises(ValueError):
            strip_palette("const newLayout = { path: '/sponsors' };\n")
        with self.assertRaises(ValueError):
            replace('one one', 'one')


if __name__ == '__main__':
    unittest.main()
