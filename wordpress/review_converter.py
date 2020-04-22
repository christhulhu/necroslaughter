import re

from bs4 import BeautifulSoup


class ReviewConverter:
    def __init__(self, known_labels, normalized_labels):
        self.known_labels = known_labels
        self.normalized_labels = normalized_labels

    def convert(self, post):
        content = post.content
        content = self.strip_old_ratings(content)
        content = self.strip_old_review_divs(content)
        content = self.strip_whitespaces(content)

        if 'DEATHRITE - Über Labeldeals, Albumproduktion und verkorkste Tourneen' != (post.title):
            new_content = ''
            meta_content = ''
            info_block = False
            for line in content.splitlines():
                if line.lower().startswith('**info') or ('****' in line) or line == '---'  or line == '--':
                    info_block = True
                if not info_block:
                    new_content += line + '\n'
                else:
                    meta_content += line + '\n'
            #if not info_block:
            #    print(post.title)
            content = new_content
            post.raw_meta = meta_content

        post.content = content

        post = self.strip_links_from_meta(post)
        post = self.process_meta(post)
        return post

    def strip_links_from_meta(self, post):
        if post.raw_meta:
            new_meta = ''
            links = []
            for line in post.raw_meta.splitlines():
                if line != '' and line != '---' and line != '--' and not line == '****' and not line.lower().startswith('**info'):
                    if line.startswith('<iframe') \
                            or line.startswith('<img') \
                            or line.startswith('<script') \
                            or line.startswith('$(function') \
                            or line.startswith('// ]]>') \
                            or line.startswith('Auf Amazon')\
                            or line.startswith('Kaufen bei'):
                        pass
                    elif line.startswith('<a') or line.startswith('http'):
                        self.append_if_not(post.links, line)
                    else:
                        new_meta += line + '\n'
            post.raw_meta = new_meta
        return post

    def strip_whitespaces(self, content):
        new_content = ''
        for line in content.splitlines():
            new_content += line.strip() + '\n'
        content = new_content
        return content

    def strip_old_review_divs(self, content):
        soup = BeautifulSoup(content, 'lxml')
        review_div = soup.find('div', {'class', 'review'})
        if review_div:
            new_content = ''
            for c in review_div.contents:
                new_content += str(c)
            content = new_content
        return content

    def strip_old_ratings(self, content):
        content = re.sub('\[rating:.+\]', '', content)
        return content

    def extract_formats(self, line, post):
        if not post.formats:
            post.formats = []

        if "cdr" in line.lower():
            self.append_if_not(post.formats, "CDr")
        elif "cd-r" in line.lower():
            self.append_if_not(post.formats, "CDr")
        elif "split-cd" in line.lower():
            self.append_if_not(post.formats, "CD")
        elif "cd" in line.lower():
            self.append_if_not(post.formats, "CD")

        if 'digipak' in line.lower():
            self.append_if_not(post.formats, "Digipak-CD")
        if 'lp' in line.lower():
            self.append_if_not(post.formats, "LP")
        if '12"' in line.lower():
            self.append_if_not(post.formats, "LP")
        if '7"' in line.lower():
            self.append_if_not(post.formats, "7\"")

        if 'tape' in line.lower():
            self.append_if_not(post.formats, "Kasette")
        if 'mc' in line.lower():
            self.append_if_not(post.formats, "Kasette")
        if 'kassette' in line.lower():
            self.append_if_not(post.formats, "Kasette")

    def append_if_not(self, named_list, value):
        if value not in named_list:
            named_list.append(value)

    def process_meta(self, post):
        if post.raw_meta:
            for line in post.raw_meta.splitlines():
                for label in self.known_labels:
                    if label in line:
                        if label in self.normalized_labels:
                            self.append_if_not(post.labels, self.normalized_labels[label])
                        else:
                            self.append_if_not(post.labels, label)

        return post