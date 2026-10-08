import unittest

from fetch_pytorch import links_in_scope, relative_html_path


class PytorchCrawlerTests(unittest.TestCase):
    def test_forecasting_crawl_starts_from_the_site_index(self):
        from fetch_pytorch import SITES

        self.assertEqual(SITES['pytorch-forecasting']['start_pages'], ('index.html',))

    def test_links_are_limited_to_the_versioned_html_tree(self):
        base = 'https://docs.pytorch.org/docs/2.14/'
        html = '''
        <a href="nn.html#torch.nn.Module">module</a>
        <a href="nn.html#other">duplicate page</a>
        <a href="../2.13/index.html">other release</a>
        <a href="https://example.com/docs/2.14/foreign.html">other host</a>
        <a href="_static/theme.css">asset</a>
        '''

        self.assertEqual(links_in_scope(html, base + 'index.html', base), {base + 'nn.html'})

    def test_relative_path_rejects_urls_outside_collection(self):
        base = 'https://pytorch-forecasting.readthedocs.io/en/v1.0.0/'

        self.assertEqual(relative_html_path(base + 'getting-started.html', base), 'getting-started.html')
        with self.assertRaises(ValueError):
            relative_html_path('https://pytorch-forecasting.readthedocs.io/en/latest/index.html', base)


if __name__ == '__main__':
    unittest.main()