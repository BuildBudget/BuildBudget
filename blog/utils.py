from datetime import datetime
from typing import Optional, List, Dict, NamedTuple
import markdown
import yaml
from django.conf import settings
from pathlib import Path


class BlogPost(NamedTuple):
    title: str
    slug: str
    content: str
    excerpt: str
    published_date: datetime
    raw_content: str


def get_blog_root() -> Path:
    """Returns the root directory for blog posts."""
    return Path(settings.BLOG_ROOT)


def parse_post_content(content: str) -> tuple[Dict, str]:
    """
    Parse blog post content, separating YAML front matter from markdown content.
    Expected format:
    ---
    title: Post Title
    date: 2024-01-01
    excerpt: A brief description
    ---
    Post content in markdown...
    """
    # Split content into front matter and markdown
    if content.startswith("---"):
        _, fm, content = content.split("---", 2)
        metadata = yaml.safe_load(fm)
    else:
        metadata = {}

    return metadata, content.strip()


def load_post(file_path: Path) -> Optional[BlogPost]:
    """Load and parse a single blog post file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        metadata, markdown_content = parse_post_content(content)

        # Convert markdown to HTML
        html_content = markdown.markdown(
            markdown_content, extensions=["fenced_code", "codehilite", "tables", "toc"]
        )

        # Use filename as slug if not specified in metadata
        slug = metadata.get("slug", file_path.stem)

        return BlogPost(
            title=metadata.get("title", "Untitled"),
            slug=slug,
            content=html_content,
            excerpt=metadata.get("excerpt", ""),
            published_date=metadata.get("date"),
            raw_content=markdown_content,
        )
    except Exception as e:
        print(f"Error loading post {file_path}: {e}")
        return None


def load_all_posts() -> List[BlogPost]:
    """Load all blog posts and sort them by date."""
    blog_root = get_blog_root()
    posts = []

    # Load all markdown files
    for file_path in blog_root.glob("*.md"):
        post = load_post(file_path)
        if post is not None:
            posts.append(post)

    # Sort posts by date, newest first
    return sorted(posts, key=lambda x: x.published_date, reverse=True)
