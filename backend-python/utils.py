import xml.etree.ElementTree as ET

def parse_file_content(content):
    """
    Parses structured text content with <seg>, <source>, <target> tags.

    Args:
        content: The string content of the file.

    Returns:
        A list of tuples, where each tuple is (source_text, target_text).
        Returns an empty list if parsing fails or content is empty.

    Raises:
        ET.ParseError: If the XML structure is invalid.
    """
    segments = []
    if not content or not content.strip():
        return segments

    try:
        # Wrap content in a root element for valid XML parsing
        # Use a namespace-agnostic approach for finding tags
        root = ET.fromstring(f"<root>{content}</root>")
        for seg_element in root.findall('.//seg'):
            source_element = seg_element.find('.//source')
            target_element = seg_element.find('.//target')

            source_text = source_element.text.strip() if source_element is not None and source_element.text else ""
            target_text = target_element.text.strip() if target_element is not None and target_element.text else ""

            # Only add if source text is present
            if source_text:
                segments.append((source_text, target_text))
    except ET.ParseError as e:
        print(f"XML Parse Error: {e}") # Log the error
        raise # Re-raise the error to be handled by the caller

    return segments

# Example usage and test cases
if __name__ == '__main__':
    test_content_1 = """
<seg>
  <source> This is the first paragraph. </source>
  <target> 这是第一段。 </target>
</seg>
<seg>
  <source> This is the second paragraph, with no target yet. </source>
  <target></target>
</seg>
<seg>
  <source>Third paragraph.</source>
  <target>第三段。</target>
</seg>
<seg>
  <source>  Paragraph with only source.  </source>
</seg>
"""
    print(f"Test 1 Segments: {parse_file_content(test_content_1)}")
    # Expected: [('This is the first paragraph.', '这是第一段。'), ('This is the second paragraph, with no target yet.', ''), ('Third paragraph.', '第三段。'), ('Paragraph with only source.', '')]

    test_content_2 = "<seg><source>Single segment.</source><target>单个片段。</target></seg>"
    print(f"Test 2 Segments: {parse_file_content(test_content_2)}")
    # Expected: [('Single segment.', '单个片段。')]

    test_content_3 = "" # Empty content
    print(f"Test 3 Segments: {parse_file_content(test_content_3)}")
    # Expected: []

    test_content_4 = "<seg><source>Source only.</source></seg>"
    print(f"Test 4 Segments: {parse_file_content(test_content_4)}")
    # Expected: [('Source only.', '')]

    test_content_5 = "<seg><target>Target only.</target></seg>" # Invalid segment (no source)
    print(f"Test 5 Segments: {parse_file_content(test_content_5)}")
    # Expected: []

    test_content_6 = "Just plain text, no tags." # Invalid format
    try:
        print(f"Test 6 Segments: {parse_file_content(test_content_6)}")
    except ET.ParseError as e:
        print(f"Test 6 correctly failed with ParseError: {e}")
    # Expected: ParseError

    test_content_7 = "<root><seg><source>Valid XML</source></seg></root>" # Already has root
    try:
        print(f"Test 7 Segments: {parse_file_content(test_content_7)}")
    except ET.ParseError as e:
        print(f"Test 7 failed with ParseError (double root): {e}")
    # Expected: ParseError (due to <root><root> structure)

    test_content_8 = "<seg><source>Segment 1</source><target>T1</target></seg><seg><source>Segment 2</source></seg>"
    print(f"Test 8 Segments: {parse_file_content(test_content_8)}")
    # Expected: [('Segment 1', 'T1'), ('Segment 2', '')]
