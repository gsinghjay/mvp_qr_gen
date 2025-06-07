import os
import yaml
import markdown
from functools import lru_cache
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ContentNotFoundError(Exception):
    """Raised when requested content file is not found."""
    pass

class ContentParsingError(Exception):
    """Raised when content file cannot be parsed."""
    pass

class ContentService:
    """
    Service for reading and parsing Markdown files with YAML frontmatter.
    
    This service provides content parsing capabilities for the portal system,
    following the atomic service pattern with proper error handling and caching.
    """
    
    def __init__(self, content_directory: str = "app/content/portal"):
        """
        Initialize the ContentService.
        
        Args:
            content_directory: Directory path containing the markdown content files
        """
        self.content_directory = Path(content_directory)
        self.markdown_processor = markdown.Markdown(extensions=['meta'])
    
    @lru_cache(maxsize=128)
    def get_page_data(self, page_path: str) -> Dict[str, Any]:
        """
        Get page data from a Markdown file with YAML frontmatter.
        
        This method reads the specified Markdown file, parses its YAML frontmatter,
        and converts the markdown content to HTML. Results are cached for performance.
        
        Args:
            page_path: Path to the page (relative to content directory, without .md extension)
            
        Returns:
            Dictionary containing parsed metadata and HTML content:
            {
                'meta': dict,     # Parsed YAML frontmatter
                'content': str    # HTML content from markdown
            }
            
        Raises:
            ContentNotFoundError: If the requested file does not exist
            ContentParsingError: If the file cannot be parsed
        """
        try:
            # Construct the full file path
            file_path = self.content_directory / f"{page_path.strip('/')}.md"
            
            # Check if file exists
            if not file_path.exists():
                logger.warning(f"Content file not found: {file_path}")
                raise ContentNotFoundError(f"Content file not found: {page_path}")
            
            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Parse YAML frontmatter manually
            meta = {}
            markdown_content = content
            
            if content.startswith('---'):
                # Split frontmatter and content
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1].strip()
                    markdown_content = parts[2].strip()
                    
                    # Parse YAML frontmatter
                    if frontmatter:
                        try:
                            meta = yaml.safe_load(frontmatter) or {}
                        except yaml.YAMLError as e:
                            logger.error(f"YAML parsing error in {page_path}: {str(e)}")
                            raise ContentParsingError(f"YAML parsing error: {str(e)}")
            
            # Reset the markdown processor for fresh parsing
            self.markdown_processor.reset()
            
            # Convert markdown content to HTML
            html_content = self.markdown_processor.convert(markdown_content)
            
            logger.info(f"Successfully parsed content for page: {page_path}")
            
            return {
                'meta': meta,
                'content': html_content
            }
            
        except FileNotFoundError:
            logger.warning(f"Content file not found: {page_path}")
            raise ContentNotFoundError(f"Content file not found: {page_path}")
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in {page_path}: {str(e)}")
            raise ContentParsingError(f"YAML parsing error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error parsing content {page_path}: {str(e)}")
            raise ContentParsingError(f"Error parsing content: {str(e)}")
    
    def clear_cache(self) -> None:
        """
        Clear the LRU cache for page data.
        
        This is useful during development or when content files are updated
        and you need to force a refresh of cached content.
        """
        self.get_page_data.cache_clear()
        logger.info("Content cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about the current cache state.
        
        Returns:
            Dictionary with cache statistics including hits, misses, maxsize, and currsize
        """
        cache_info = self.get_page_data.cache_info()
        return {
            'hits': cache_info.hits,
            'misses': cache_info.misses,
            'maxsize': cache_info.maxsize,
            'currsize': cache_info.currsize
        }
    
    def list_available_pages(self) -> list[str]:
        """
        List all available markdown pages in the content directory.
        
        Returns:
            List of page paths (without .md extension) that can be requested
        """
        try:
            if not self.content_directory.exists():
                return []
            
            pages = []
            for file_path in self.content_directory.rglob("*.md"):
                # Convert to relative path and remove .md extension
                relative_path = file_path.relative_to(self.content_directory)
                page_path = str(relative_path).replace('.md', '')
                pages.append(page_path)
            
            return sorted(pages)
            
        except Exception as e:
            logger.error(f"Error listing available pages: {str(e)}")
            return [] 