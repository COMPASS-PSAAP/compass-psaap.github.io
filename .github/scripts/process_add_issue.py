#!/usr/bin/env python3
"""
Process "Add person" and "Add project" GitHub issue submissions.
Parses the issue body generated from GitHub Issue Forms, generates or updates
the appropriate files expected by the Greene Lab Website Template,
and exports step outputs for GitHub Actions.
"""

import os
import re
import sys
import yaml
from pathlib import Path


def parse_issue_form(body: str) -> dict:
    """
    Parse a GitHub Issue Form markdown body.
    Issue forms render as:
    ### Header Name
    
    Content here
    
    ### Another Header
    ...
    """
    fields = {}
    current_key = None
    current_lines = []

    for line in body.splitlines():
        header_match = re.match(r"^###\s+(.+)$", line)
        if header_match:
            if current_key:
                fields[current_key] = "\n".join(current_lines).strip()
            current_key = header_match.group(1).strip()
            current_lines = []
        else:
            if current_key:
                current_lines.append(line)

    if current_key:
        fields[current_key] = "\n".join(current_lines).strip()

    # Clean up fields: GitHub sets empty fields to '_No response_'
    cleaned = {}
    for k, v in fields.items():
        val = v.strip()
        if val == "_No response_" or val == "_None_":
            val = ""
        cleaned[k] = val

    return cleaned


def slugify(text: str) -> str:
    """Generate a clean slug for file naming (e.g. 'Jane Doe' -> 'jane-doe')."""
    text = text.strip()
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text)
    return slug.strip("-").lower()


def parse_links(raw_links: str) -> dict:
    """
    Extract structured links (email, orcid, github, linkedin, twitter, homepage/website)
    from freeform input.
    """
    if not raw_links:
        return {}

    links = {}
    # Split by newlines or commas
    tokens = [t.strip() for t in re.split(r"[\n,]+", raw_links) if t.strip()]

    for token in tokens:
        # Email check
        if re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", token):
            links["email"] = token
            continue

        # ORCID check
        orcid_match = re.search(r"(\d{4}-\d{4}-\d{4}-[\dX]{4})", token)
        if orcid_match:
            links["orcid"] = orcid_match.group(1)
            continue

        # GitHub check
        gh_match = re.search(r"github\.com/([A-Za-z0-9_.-]+)", token)
        if gh_match:
            links["github"] = gh_match.group(1)
            continue

        # LinkedIn check
        li_match = re.search(r"linkedin\.com/in/([A-Za-z0-9_.-]+)", token)
        if li_match:
            links["linkedin"] = li_match.group(1)
            continue

        # Twitter / X check
        tw_match = re.search(r"(?:twitter|x)\.com/([A-Za-z0-9_]+)", token)
        if tw_match:
            links["twitter"] = tw_match.group(1)
            continue

        # Google Scholar check
        if "scholar.google.com" in token:
            links["google-scholar"] = token
            continue

        # General URL
        if token.startswith("http://") or token.startswith("https://"):
            if "home-page" not in links:
                links["home-page"] = token
            elif "website" not in links:
                links["website"] = token
            else:
                links["link"] = token

    return links


def categorize_role(role_input: str) -> str:
    """
    Map user input role to one of the 4 category keys used in team/index.md:
    'principal-investigator', 'programmer', 'student', 'admin'.
    """
    r = role_input.lower().strip()
    if any(k in r for k in ["investigator", "pi", "co-pi", "director", "professor", "faculty"]):
        return "principal-investigator"
    if any(k in r for k in ["student", "phd", "undergrad", "grad", "doctoral", "master"]):
        return "student"
    if any(k in r for k in ["admin", "manager", "coordinator", "assistant"]):
        return "admin"
    # Default category for staff, developers, engineers, scientists, postdocs
    return "programmer"


def process_person(fields: dict, repo_root: Path) -> dict:
    """
    Process 'Add person' fields and create _members/<slug>.md
    """
    name = fields.get("Name", "").strip()
    if not name:
        raise ValueError("Missing required field 'Name'")

    affiliation = fields.get("Affiliation", "").strip()
    raw_role = fields.get("Role", "").strip() or "Staff Research Scientist"
    role_category = categorize_role(raw_role)
    description = raw_role

    image = fields.get("Image", "").strip()
    if image and not image.startswith("images/") and not image.startswith("http"):
        image = f"images/{image}"

    raw_links = fields.get("Email or links", "").strip()
    links = parse_links(raw_links)

    notes = fields.get("Notes", "").strip()

    slug = slugify(name)
    members_dir = repo_root / "_members"
    members_dir.mkdir(parents=True, exist_ok=True)
    target_file = members_dir / f"{slug}.md"

    # Build frontmatter dict
    fm = {
        "name": name,
        "image": image,
        "description": description,
        "role": role_category,
        "affiliation": affiliation,
    }
    if links:
        fm["links"] = links

    # Format Markdown file
    yaml_header = yaml.dump(fm, sort_keys=False, default_flow_style=False).strip()
    content = f"---\n{yaml_header}\n---\n"
    if notes:
        content += f"\n{notes}\n"

    target_file.write_text(content, encoding="utf-8")

    return {
        "action_type": "person",
        "item_name": name,
        "target_file": str(target_file.relative_to(repo_root)),
        "branch_name": f"add-person-{slug}",
        "pr_title": f"Add person: {name}",
    }


def process_project(fields: dict, repo_root: Path) -> dict:
    """
    Process 'Add project' fields and append to _data/projects.yaml
    """
    title = fields.get("Title", "").strip()
    if not title:
        raise ValueError("Missing required field 'Title'")

    description = fields.get("Short description", "").strip()
    if not description:
        raise ValueError("Missing required field 'Short description'")

    subtitle = fields.get("Subtitle", "").strip()
    link = fields.get("Link", "").strip()
    repo = fields.get("Repo", "").strip()
    image = fields.get("Image", "").strip() or "images/photo.jpg"
    raw_tags = fields.get("Tags", "").strip()

    tags = []
    if raw_tags:
        tags = [t.strip() for t in re.split(r"[, ]+", raw_tags) if t.strip()]

    projects_file = repo_root / "_data" / "projects.yaml"
    projects_file.parent.mkdir(parents=True, exist_ok=True)

    # Load existing projects or initialize
    if projects_file.exists() and projects_file.stat().st_size > 0:
        existing = yaml.safe_load(projects_file.read_text(encoding="utf-8")) or []
    else:
        existing = []

    # Construct new project entry
    new_project = {
        "title": title,
    }
    if subtitle:
        new_project["subtitle"] = subtitle
    new_project["image"] = image
    if link:
        new_project["link"] = link
    new_project["description"] = description
    if repo:
        new_project["repo"] = repo
    if tags:
        new_project["tags"] = tags

    existing.append(new_project)

    # Format cleanly with separation between list items
    formatted_yaml = yaml.dump(
        existing,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
    )
    # Ensure standard clean formatting for top-level list items
    formatted_yaml = re.sub(r"\n- title:", r"\n\n- title:", formatted_yaml).strip() + "\n"
    projects_file.write_text(formatted_yaml, encoding="utf-8")

    slug = slugify(title)
    return {
        "action_type": "project",
        "item_name": title,
        "target_file": str(projects_file.relative_to(repo_root)),
        "branch_name": f"add-project-{slug}",
        "pr_title": f"Add project: {title}",
    }


def main():
    body = os.environ.get("ISSUE_BODY", "")
    title = os.environ.get("ISSUE_TITLE", "")
    number = os.environ.get("ISSUE_NUMBER", "0")
    repo_root = Path(os.environ.get("REPO_ROOT", ".")).resolve()

    if not body:
        print("No ISSUE_BODY provided. Nothing to process.")
        sys.exit(0)

    fields = parse_issue_form(body)

    # Determine whether person or project
    is_person = "Add person" in title or ("Name" in fields and "Affiliation" in fields)
    is_project = "Add project" in title or ("Title" in fields and "Short description" in fields)

    if is_person:
        result = process_person(fields, repo_root)
    elif is_project:
        result = process_project(fields, repo_root)
    else:
        print("Issue did not match 'Add person' or 'Add project' templates.")
        sys.exit(0)

    # Append issue number to branch name to ensure uniqueness
    if number and number != "0":
        result["branch_name"] = f"{result['branch_name']}-{number}"

    result["created"] = "true"

    # Write to GITHUB_OUTPUT if available
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            for k, v in result.items():
                f.write(f"{k}={v}\n")

    print(f"Successfully processed {result['action_type']}: {result['item_name']}")
    print(f"Target file: {result['target_file']}")
    print(f"Branch: {result['branch_name']}")
    print(f"PR Title: {result['pr_title']}")


if __name__ == "__main__":
    main()
