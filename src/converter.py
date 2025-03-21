from textnode import TextNode, TextType
from htmlnode import LeafNode
from htmlnode import HTMLNode
from split_nodes_delimiter import split_nodes_delimiter
import os
import re
from enum import Enum
import unittest

def text_node_to_html_node(text_node):
    if text_node.text_type == TextType.TEXT:
        return LeafNode(None, text_node.text)
    if text_node.text_type == TextType.BOLD:
        return LeafNode("b", text_node.text)
    if text_node.text_type == TextType.ITALIC:
        return LeafNode("i", text_node.text)
    if text_node.text_type == TextType.CODE:
        return LeafNode("code", text_node.text)
    if text_node.text_type == TextType.LINK:
        return LeafNode("a", text_node.text, {"href": text_node.url})
    if text_node.text_type == TextType.IMAGE:
        return LeafNode("img", "", {"src": text_node.url, "alt": text_node.text})
    else:
        raise Exception("Invaild TextType")

def extract_markdown_images(text):
    pattern = r"!\[([^\[\]]*)\]\(([^\(\)]*)\)"
    matches = re.findall(pattern, text)
    return matches
    
def extract_markdown_links(text):
    pattern = r"(?<!!)\[([^\[\]]*)\]\(([^\(\)]*)\)"
    matches = re.findall(pattern, text)
    return matches
    
def split_nodes_image(old_nodes):
    result = []
    
    for node in old_nodes:
        if node.text_type != TextType.TEXT:
            result.append(node)
            continue
            
        text = node.text
        images = extract_markdown_images(text)
        
        if not images:
            result.append(node)
            continue
        
        current_text = text
        for image_alt, image_url in images:
            image_markdown = f"![{image_alt}]({image_url})"
            sections = current_text.split(image_markdown, 1)
            
            if sections[0]:
                result.append(TextNode(sections[0], TextType.TEXT))
            
            result.append(TextNode(image_alt, TextType.IMAGE, image_url))
            
            if len(sections) > 1:
                current_text = sections[1]
            else:
                current_text = ""
        
        if current_text:
            result.append(TextNode(current_text, TextType.TEXT))
    
    return result
    
def split_nodes_link(old_nodes):
    result = []
    
    for node in old_nodes:
        if node.text_type != TextType.TEXT:
            result.append(node)
            continue
            
        text = node.text
        links = extract_markdown_links(text)
        
        if not links:
            result.append(node)
            continue
    
        current_text = text
        for link_text, link_url in links:
            link_markdown = f"[{link_text}]({link_url})"
            sections = current_text.split(link_markdown, 1)
            
            if sections[0]:
                result.append(TextNode(sections[0], TextType.TEXT))
            
            result.append(TextNode(link_text, TextType.LINK, link_url))
            
            if len(sections) > 1:
                current_text = sections[1]
            else:
                current_text = ""
        
        if current_text:
            result.append(TextNode(current_text, TextType.TEXT))
    
    return result
    
def markdown_to_block(markdown):
    blocks = markdown.split("\n\n")
    result = []
    for block in blocks:
        stripped_block = block.strip()
        if stripped_block:
            result.append(stripped_block)
    return result
    
BlockType = Enum('BlockType', ['paragraph', 'heading', 'code', 'quote', 'unordered_list', 'ordered_list'])

def block_to_block_type(text):
    if re.match(r'^#{1,6} ', text):
        return BlockType.heading
        
    if text.startswith('```') and text.endswith('```'):
        return BlockType.code
    
    lines = text.split('\n')
        
    if all(line.startswith('>') for line in lines):
        return BlockType.quote
        
    if all(line.startswith('- ') for line in lines):
        return BlockType.unordered_list
        
    is_ordered_list = True
    for i, line in enumerate(lines, 1):
        expected_prefix = f"{i}. "
        if not line.startswith(expected_prefix):
            is_ordered_list = False
            break
    
    if is_ordered_list:
        return BlockType.ordered_list
        
    return BlockType.paragraph

def text_to_children(text):
    text_node = TextNode(text, "text")
    
    nodes = [text_node]
    nodes = split_nodes_delimiter(nodes, "**", "bold")
    nodes = split_nodes_delimiter(nodes, "_", "italic")
    nodes = split_nodes_delimiter(nodes, "`", "code")
    
    html_nodes = []
    for node in nodes:
        html_node = text_node_to_html_node(node)
        html_nodes.append(html_node)
    
    return html_nodes
    
def markdown_to_html_node(markdown):
    blocks = markdown_to_block(markdown)
    parent = HTMLNode("div", "", [])
    
    for block in blocks:
        block_type = block_to_block_type(block)
        
        if block_type == "paragraph":

            children = text_to_children(block)
  
            p_node = HTMLNode("p", "", children)

            parent.children.append(p_node)
            
        elif block_type == "heading":
            level = 0
            for char in block:
                if char == '#':
                    level += 1
                else:
                    break
            level = min(level, 6)
            
            heading_text = block.lstrip('#').strip()
            children = text_to_children(heading_text)
            
            h_node = HTMLNode(f"h{level}", "", children)
            parent.children.append(h_node)
            
        elif block_type == "code":
            code_text = block.strip('`').strip()
            text_node = TextNode(code_text, "text")
            code_html = text_node_to_html_node(text_node)
    
            code_node = HTMLNode("code", "", [code_html])
            pre_node = HTMLNode("pre", "", [code_node])
            parent.children.append(pre_node)
            
        elif block_type == "quote":
            quote_text = block.lstrip('>').strip()
            children = text_to_children(quote_text)
            quote_node = HTMLNode("blockquote", "", children)
            parent.children.append(quote_node)
            
        elif block_type == "unordered_list":
            items = block.split('\n')
            list_items = []
            for item in items:
                item_text = item.lstrip('*- ').strip()
                if item_text:
                    children = text_to_children(item_text)
                    li_node = HTMLNode("li", "", children)
                    list_items.append(li_node)
    
            ul_node = HTMLNode("ul", "", list_items)
            parent.children.append(ul_node)

        elif block_type == "ordered_list":
            items = block.split('\n')
            list_items = []
            for item in items:
                # Remove the digit and period from the beginning
                item_text = ''.join(item.split('.')[1:]).strip()
                if item_text:
                    children = text_to_children(item_text)
                    li_node = HTMLNode("li", "", children)
                    list_items.append(li_node)
    
            ol_node = HTMLNode("ol", "", list_items)
            parent.children.append(ol_node)
    return parent

def extract_title(markdown):
    lines = markdown.split("\n")
    for line in lines:
        if line.strip().startswith("# "):
            return line.strip()[2:].strip()
    raise Exception("No h1 header found in markdown")
    
def generate_page(from_path, template_path, dest_path):
    print(f"Generating page from {from_path} to {dest_path} using {template_path}")
    
    # Check if all paths exist
    print(f"Does from_path exist? {os.path.exists(from_path)}")
    print(f"Does template_path exist? {os.path.exists(template_path)}")
    
    with open(from_path, 'r') as f:
        markdown_content = f.read()
        print(f"Read {len(markdown_content)} characters from markdown file")
    
    with open(template_path, 'r') as f:
        template_content = f.read()
        print(f"Read {len(template_content)} characters from template file")
    
    html_node = markdown_to_html_node(markdown_content)
    html_content = html_node.to_html()
    print(f"Generated HTML content: {html_content[:100]}...")  # Print first 100 chars
    
    title = extract_title(markdown_content)
    print(f"Extracted title: {title}")
    
    final_html = template_content.replace("{{ Title }}", title)
    final_html = final_html.replace("{{ Content }}", html_content)
    
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    with open(dest_path, 'w') as f:
        f.write(final_html)
    
    # Verify the file was created
    print(f"Does dest_path exist after generation? {os.path.exists(dest_path)}")
    print(f"Size of generated file: {os.path.getsize(dest_path)} bytes")
            
class TestBlockToBlockType(unittest.TestCase):
    def test_paragraph(self):
        text = "This is a simple paragraph with no special formatting."
        self.assertEqual(block_to_block_type(text), BlockType.paragraph)
        
    def test_heading(self):
        self.assertEqual(block_to_block_type("# Heading 1"), BlockType.heading)
        self.assertEqual(block_to_block_type("## Heading 2"), BlockType.heading)
        self.assertEqual(block_to_block_type("###### Heading 6"), BlockType.heading)
        
    def test_code(self):
        self.assertEqual(block_to_block_type("```\nprint('Hello World')\n```"), BlockType.code)
        
    def test_quote(self):
        self.assertEqual(block_to_block_type(">This is a quote"), BlockType.quote)
        self.assertEqual(block_to_block_type(">Line 1\n>Line 2"), BlockType.quote)
        
    def test_unordered_list(self):
        self.assertEqual(block_to_block_type("- Item 1"), BlockType.unordered_list)
        self.assertEqual(block_to_block_type("- Item 1\n- Item 2\n- Item 3"), BlockType.unordered_list)
        
    def test_ordered_list(self):
        self.assertEqual(block_to_block_type("1. Item 1"), BlockType.ordered_list)
        
class TestExtractTitle(unittest.TestCase):

    def test_simple_title(self):
        markdown = "# Hello World"
        self.assertEqual(extract_title(markdown), "Hello World")
    
    def test_title_with_whitespace(self):
        markdown = "#     Extra Spaces    "
        self.assertEqual(extract_title(markdown), "Extra Spaces")
    
    def test_title_with_other_content(self):
        markdown = "Some text before\n# The Real Title\nSome text after"
        self.assertEqual(extract_title(markdown), "The Real Title")
    
    def test_multiple_headers(self):
        # Should return the first H1 header
        markdown = "# First Title\n## Second Level\n# Another Title"
        self.assertEqual(extract_title(markdown), "First Title")
    
    def test_no_h1_header(self):
        markdown = "No header here\nJust plain text"
        with self.assertRaises(Exception):
            extract_title(markdown)
    
    def test_wrong_header_format(self):
        markdown = "#Wrong Format (no space after #)"
        with self.assertRaises(Exception):
            extract_title(markdown)

if __name__ == "__main__":
    unittest.main()