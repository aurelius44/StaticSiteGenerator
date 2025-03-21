from textnode import TextNode, TextType

def split_nodes_delimiter(old_nodes, delimiter, text_type):
    result = []
    for node in old_nodes:
        if node.text_type != TextType.TEXT:
            result.append(node)
            continue
            
        text = node.text
        if delimiter not in text:
            result.append(node)
            continue
            
        start_index = text.find(delimiter)
        end_index = text.find(delimiter, start_index + len(delimiter))
        
        if end_index == -1:
            raise Exception(f"No closing delimiter found for {delimiter}")
        
        before_text = text[:start_index]
        between_text = text[start_index + len(delimiter):end_index]
        after_text = text[end_index + len(delimiter):]
        
        if before_text:
            result.append(TextNode(before_text, TextType.TEXT))
            
        result.append(TextNode(between_text, text_type))
        
        if after_text:
            result.append(TextNode(after_text, TextType.TEXT))
    
    return result