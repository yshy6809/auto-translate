import re

def parse_file_content(content):
    """将文本内容分割为段落"""
    # 1. Split the content using a regular expression:
    #    re.split(r'\n\s*\n+', content)
    #    - r'\n\s*\n+' matches one newline (\n), followed by
    #      zero or more whitespace characters (\s*), followed by
    #      one or more newlines (\n+).
    #    - This effectively splits the text wherever there are one or more blank lines
    #      (or lines containing only whitespace) between paragraphs.
    #
    # 2. Iterate through the resulting list of potential segments:
    #    [... for segment in ... ]
    #
    # 3. For each segment, remove leading/trailing whitespace:
    #    segment.strip()
    #
    # 4. Filter out any segments that are empty after stripping:
    #    ... if segment.strip()
    #
    # 5. Return the final list of non-empty, stripped segments.
    return [segment.strip() for segment in re.split(r'\n\s*\n+', content) if segment.strip()]

# Example usage and test cases (optional, but good practice)
if __name__ == '__main__':
    test_content_1 = "Paragraph 1.\n\nParagraph 2.\n  \nParagraph 3."
    print(f"Test 1 Segments: {parse_file_content(test_content_1)}")
    # Expected: ['Paragraph 1.', 'Paragraph 2.', 'Paragraph 3.']

    test_content_2 = "Single paragraph."
    print(f"Test 2 Segments: {parse_file_content(test_content_2)}")
    # Expected: ['Single paragraph.']

    test_content_3 = "\n\n   \nLeading and trailing whitespace.\n\n   \n\n"
    print(f"Test 3 Segments: {parse_file_content(test_content_3)}")
    # Expected: ['Leading and trailing whitespace.']

    test_content_4 = ""
    print(f"Test 4 Segments: {parse_file_content(test_content_4)}")
    # Expected: []

    test_content_5 = "Line1\nLine2\n\nLine3" # Treat consecutive newlines as separator
    print(f"Test 5 Segments: {parse_file_content(test_content_5)}")
    # Expected: ['Line1\nLine2', 'Line3']

    test_content_6 = "段落一。\n\n段落二。\n\n   \n\n段落三。"
    print(f"Test 6 Segments (Chinese): {parse_file_content(test_content_6)}")
    # Expected: ['段落一。', '段落二。', '段落三。']
