#!/usr/bin/env python3
import os
import urllib.parse
from datetime import datetime


def load_gitignore_patterns(wiki_dir):
    """Load patterns from .gitignore file if it exists"""
    gitignore_path = os.path.join(wiki_dir, '.gitignore')
    patterns = []

    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            for line in f:
                # Remove comments and empty lines
                line = line.split('#')[0].strip()
                if line:
                    patterns.append(line)

    return patterns

def should_ignore(path, gitignore_patterns):
    """Check if a path should be ignored based on gitignore patterns"""
    path_str = str(path)

    # Simple implementation of gitignore pattern matching
    for pattern in gitignore_patterns:
        # Handle directory-specific patterns
        if pattern.endswith('/') and os.path.isdir(path):
            if path_str.endswith(pattern[:-1]) or f"{path_str}/" in pattern:
                return True
        # Handle wildcard patterns (simplified)
        elif '*' in pattern:
            parts = pattern.split('*')
            if len(parts) == 2 and path_str.startswith(parts[0]) and path_str.endswith(parts[1]):
                return True
        # Direct match
        elif pattern in path_str:
            return True

    return False

def clean_filename(filename):
    # Remove file extension if present
    name = os.path.splitext(filename)[0]
    # Replace hyphens and underscores with spaces for better readability
    name = name.replace('-', ' ').replace('_', ' ')
    return name

def generate_wiki_link(filename):

    # GitHub Wiki links use the filename (without extension) as the page name
    # Spaces in filenames are represented as hyphens in Wiki URLs
    name = os.path.splitext(filename)[0]
    link_name = clean_filename(filename)
    link_url = name.replace(' ', '-')
    link_url = urllib.parse.quote(link_url)
    return f"[{link_name}]({link_url})"

def generate_sidebar(wiki_dir='.', output_file="_Sidebar.md"):
    """
    Generates a GitHub Wiki sidebar markdown file based on the directory structure.

    Args:
wiki_dir: The root directory of your wiki files (default: current directory)
output_file: The name of the output file (default: _Sidebar.md)
    """
    wiki_dir = os.path.abspath(wiki_dir)
    gitignore_patterns = load_gitignore_patterns(wiki_dir)

    # List to store the sidebar content
    sidebar_content = []

    # Add Home link at the top
    sidebar_content.append("### [[Home]]")
    sidebar_content.append("")

    # Get all directories at the root level and sort them
    root_items = sorted(os.listdir(wiki_dir))
    directories = [item for item in root_items if os.path.isdir(os.path.join(wiki_dir, item))
                   and not item.startswith('.')
                   and not should_ignore(os.path.join(wiki_dir, item), gitignore_patterns)]

    # Collect root-level markdown files for later
    root_md_files = [item for item in root_items if os.path.isfile(os.path.join(wiki_dir, item))
                     and item.endswith('.md')
                     and not item.startswith('_')  # Skip special files like _Sidebar.md
                     and not item.startswith('.')
                     and not item == "Home.md"  # Skip Home.md as it's already at the top
                     and not should_ignore(os.path.join(wiki_dir, item), gitignore_patterns)]

    # Process directories
    for directory in directories:
        directory_path = os.path.join(wiki_dir, directory)

        # Skip if it should be ignored
        if should_ignore(directory_path, gitignore_patterns):
            continue

        # Check if the directory contains any .md files (directly or in subdirectories)
        has_md_files = False
        for root, _, files in os.walk(directory_path):
            if any(f.endswith('.md') for f in files):
                has_md_files = True
                break

        if not has_md_files:
            continue

        # Add the top-level directory as a header
        clean_dir_name = clean_filename(directory)
        sidebar_content.append(f"### {clean_dir_name}")

        # Process all files and subdirectories within this directory
        process_directory(directory_path, sidebar_content, 1, gitignore_patterns)

        # Add a separator between top-level sections
        sidebar_content.append("")

    # Add root-level markdown files under "Unsorted" section
    if root_md_files:
        sidebar_content.append("### Unsorted")
        for file in sorted(root_md_files):
            wiki_link = generate_wiki_link(file)
            sidebar_content.append(f"- {wiki_link}")

    # Write the sidebar content to the output file
    # sidebar inside wiki folder
    output_path = os.path.join(wiki_dir, output_file)
    with open(output_path, 'w', encoding="utf-8") as f:
        f.write("\n".join(sidebar_content))

    print(f"Sidebar generated at: {output_path}")

def process_directory(directory_path, sidebar_content, level, gitignore_patterns):
    """
Process a directory and append its contents to the sidebar_content list.

Args:
directory_path: Path to the directory to process
sidebar_content: List to append content to
level: Current indent level (0 = top level)
gitignore_patterns: List of patterns from .gitignore
    """
    indent = "  " * level

    # Get all items in the directory and sort them
    items = sorted(os.listdir(directory_path))

    # Process files first
    files = [item for item in items if os.path.isfile(os.path.join(directory_path, item))
             and item.endswith('.md')
             and not item.startswith("_")
             and not item.startswith(".")
             and not should_ignore(os.path.join(directory_path, item), gitignore_patterns)]

    for file in files:
        # Generate a link for each file and add it to the sidebar
        wiki_link = generate_wiki_link(file)
        sidebar_content.append(f"{indent}- {wiki_link}")

    # Then process subdirectories
    subdirs = [item for item in items if os.path.isdir(os.path.join(directory_path, item))
               and not item.startswith('.')
               and not should_ignore(os.path.join(directory_path, item), gitignore_patterns)]

    for subdir in subdirs:
        subdir_path = os.path.join(directory_path, subdir)

        # Check if the directory contains any .md files (directly or in subdirectories)
        has_md_files = False
        for root, _, files in os.walk(subdir_path):
            if any(f.endswith('.md') for f in files if not should_ignore(os.path.join(root, f), gitignore_patterns)):
                has_md_files = True
                break

        if not has_md_files:
            continue

        # Add the subdirectory as a subheader
        clean_subdir_name = clean_filename(subdir)
        sidebar_content.append(f"{indent}- **{clean_subdir_name}**")

        # Process the subdirectory
        process_directory(subdir_path, sidebar_content, level + 1, gitignore_patterns)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate a GitHub Wiki sidebar from directory structure")
    parser.add_argument("--wiki-dir", "-d", default=".",
                        help="Path to your wiki directory (default: current directory)")
    parser.add_argument("--output", "-o", default="_Sidebar.md",
                        help="Output filename (default: _Sidebar.md)")

    args = parser.parse_args()

    if not os.path.isdir(args.wiki_dir):
        print(f"Error: {args.wiki_dir} is not a valid directory")
        exit(1)

    generate_sidebar(args.wiki_dir, args.output)