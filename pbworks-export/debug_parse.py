import sys
from html.parser import HTMLParser

class TagReporter(HTMLParser):
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if attrs_dict.get('id') or attrs_dict.get('class'):
            print(f"Tag: {tag}, ID: {attrs_dict.get('id')}, Class: {attrs_dict.get('class')}")

file_path = "/Users/juanpablo/2026/Estelar/website/pbworks-export/pages/107491539__Prácticas.html"
with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()
    reporter = TagReporter()
    reporter.feed(text)
