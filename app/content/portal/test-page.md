---
title: Test Portal Page
description: A test page to validate the ContentService implementation
author: Observatory Prime
page_type: test
tags:
  - test
  - portal
  - markdown
created_date: 2024-01-15
---

# Test Portal Page

This is a **test page** to validate the ContentService implementation.

## Features

- YAML frontmatter parsing
- Markdown to HTML conversion
- LRU cache for performance
- Proper error handling

## Code Example

```python
# This is how you would use the ContentService
service = ContentService()
page_data = service.get_page_data("test-page")
print(page_data['meta']['title'])  # "Test Portal Page"
```

## Links and Lists

- [Test Link](https://example.com)
- Another list item
- Third item

### Conclusion

If you can see this rendered properly, the ContentService is working correctly! 