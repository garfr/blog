#!/bin/python3

from pprint import pprint
from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode
from markdown_it.renderer import RendererHTML
from datetime import datetime
import glob, os

def log_err(filename, msg):
    print(filename + ': ' + msg)
    quit()
    
class CustomRenderer(RendererHTML):
    text_passed = 0

    def text(self, tokens, idx, options, env):
        self.text_passed = self.text_passed + 1
        if self.text_passed > 2:
            return super().text(tokens, idx, options, env)
        return ""
    
md = MarkdownIt(renderer_cls=CustomRenderer)

heading = open('heading.html', 'r').read()
posts = []

for filename in glob.glob('*.md'):
    ifile = open(filename, 'r')
    data = ifile.read()
    ifile.close()
    
    tokens = md.parse(data)
    tree = SyntaxTreeNode(tokens)

    items = tree.children
    title = items[0].children[0].children[0].content

    date_node = items[1].children[0].children[0]
    date_str = date_node.content
    date = datetime.strptime(date_str, '%m/%d/%y')

    nfilename = os.path.splitext(filename)[0] + ".html"
    
    posts.append((date, title, nfilename))
    
    ofile = open(nfilename, 'w')
    
    ofile.write(heading)
    ofile.write('<div id="post_name"><a href="' + nfilename + '">' + title + '</a></div>')
    ofile.write('<div id="post_date">' + date.strftime('%B %-d, %Y') + '</div>')
    ofile.write('<br><div id="generated">')
    ofile.write(md.render(data))
    ofile.write('</div></div></body></html>')

    ofile.close()
    
posts.sort(key=lambda post: post[0])

hfile = open('index.html', 'w')
hfile.write('<html>')
hfile.write(heading)

for (date, title, filename) in posts:

    hfile.write('<div id="post_name"><a href="' + filename + '">' + title + '</a></div>')
    hfile.write('<div id="post_date">' + date.strftime('%B %-d, %Y') + '</div>')

hfile.write('</div></body>')
hfile.write('</html>')
hfile.close()
