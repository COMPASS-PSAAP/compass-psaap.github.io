#!/usr/bin/env python3
import os
import re
import sys
import urllib.request
import urllib.parse
from io import StringIO
from pathlib import Path
from ruamel.yaml import YAML


def parse_issue_form(body: str) -> dict:
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
    
    cleaned = {}
    for k, v in fields.items():
        val = v.strip()
        if val == "_No response_" or val == "_None_":
            val = ""
        cleaned[k] = val
    return cleaned


def slugify(text: str) -> str:
    text = text.strip()
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text)
    return slug.strip("-").lower()


def parse_links(raw_links: str, email: str, home_page: str, orcid: str) -> dict:
    links = {}
    if email:
        links["email"] = email
    if home_page:
        links["home-page"] = home_page
    if orcid:
        links["orcid"] = orcid
        
    for line in raw_links.splitlines():
        line = line.strip()
        if not line: continue
        if ":" in line:
            key, val = line.split(":", 1)
            links[key.strip().lower()] = val.strip()
            
    return links


def download_image(raw_image: str, slug: str, repo_root: Path, folder: str) -> str:
    if not raw_image:
        return ""
    
    url_match = re.search(r"(https?://[^\s\)\"\']+)", raw_image)
    if not url_match:
        if not raw_image.startswith(f"{folder}/") and not raw_image.startswith("http"):
            return f"{folder}/{raw_image}"
        return raw_image

    url = url_match.group(1)
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            content = response.read()
            content_type = response.headers.get('Content-Type', '')
            
            ext = ".jpg"
            if "image/png" in content_type:
                ext = ".png"
            elif "image/gif" in content_type:
                ext = ".gif"
            elif ".png" in url.lower(): 
                ext = ".png"
            elif ".gif" in url.lower(): 
                ext = ".gif"
                
            image_path = repo_root / folder / f"{slug}-photo{ext}"
            image_path.parent.mkdir(parents=True, exist_ok=True)
            image_path.write_bytes(content)
            
        return f"{folder}/{slug}-photo{ext}"
    except Exception as e:
        print(f"Failed to download image from {url}: {e}")
        return url


def load_projects(repo_root: Path) -> list:
    projects_file = repo_root / "_data" / "projects.yaml"
    if not projects_file.exists():
        return []
    yaml = YAML()
    with open(projects_file, "r") as f:
        projects = yaml.load(f)
    return projects if projects else []


def save_projects(repo_root: Path, projects: list):
    projects_file = repo_root / "_data" / "projects.yaml"
    yaml = YAML()
    yaml.width = 4096
    yaml.default_flow_style = False
    
    buf = StringIO()
    yaml.dump(projects, buf)
    formatted_yaml = buf.getvalue()
    
    projects_file.write_text(formatted_yaml, encoding="utf-8")


def parse_markdown_frontmatter(file_path: Path):
    content = file_path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        raise ValueError(f"File {file_path} does not start with frontmatter")
    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"File {file_path} does not have valid frontmatter boundaries")
    
    yaml = YAML()
    fm = yaml.load(parts[1])
    return fm, parts[2]


def dump_markdown_frontmatter(fm: dict, content: str, target_file: Path):
    yaml = YAML()
    yaml.width = 4096
    yaml.default_flow_style = False
    buf = StringIO()
    yaml.dump(fm, buf)
    new_yaml = buf.getvalue().strip()
    new_content = f"---\n{new_yaml}\n---{content}"
    target_file.write_text(new_content, encoding="utf-8")


def process_add_person(fields: dict, repo_root: Path) -> dict:
    name = fields.get("Name", "")
    if not name: raise ValueError("Name required")
    slug = slugify(name)
    
    affiliation = fields.get("Affiliation", "")
    role_category = fields.get("Role", "programmer")
    description = fields.get("Description", "")
    
    raw_image = fields.get("Image", "")
    image = download_image(raw_image, slug, repo_root, "images/team")
    
    links = parse_links(
        fields.get("Email or links", ""), 
        fields.get("Email", ""),
        fields.get("Home page", ""),
        fields.get("ORCID", "")
    )
    
    fm = {
        "name": name,
        "description": description,
        "role": role_category,
        "affiliation": affiliation,
    }
    if image: fm["image"] = image
    if links: fm["links"] = links
    
    summary = fields.get("Personal Summary", "").strip()
    content_body = f"\n{summary}\n" if summary else "\n"
    
    target_file = repo_root / "_members" / f"{slug}.md"
    target_file.parent.mkdir(parents=True, exist_ok=True)
    dump_markdown_frontmatter(fm, content_body, target_file)
    
    return {
        "action_type": "add-person",
        "item_name": name,
        "target_file": str(target_file.relative_to(repo_root)),
        "branch_name": f"add-person-{slug}",
        "pr_title": f"Add person: {name}"
    }

def process_remove_person(fields: dict, repo_root: Path) -> dict:
    name = fields.get("Name", "")
    if not name: raise ValueError("Name required")
    
    members_dir = repo_root / "_members"
    target_file = None
    
    slug = slugify(name)
    potential_file = members_dir / f"{slug}.md"
    if potential_file.exists():
        target_file = potential_file
    else:
        for f in members_dir.glob("*.md"):
            try:
                fm, _ = parse_markdown_frontmatter(f)
                if fm and fm.get("name", "").lower() == name.lower():
                    target_file = f
                    break
            except Exception:
                pass
                
    if not target_file:
        raise ValueError(f"Could not find member file for {name}")
        
    fm, rest = parse_markdown_frontmatter(target_file)
    fm["role"] = "past-member"
    
    dump_markdown_frontmatter(fm, rest, target_file)
    
    return {
        "action_type": "remove-person",
        "item_name": name,
        "target_file": str(target_file.relative_to(repo_root)),
        "branch_name": f"remove-person-{slug}",
        "pr_title": f"Remove person: {name}"
    }


def process_add_project(fields: dict, repo_root: Path) -> dict:
    title = fields.get("Project Name", "")
    if not title: raise ValueError("Project Name required")
    
    description = fields.get("Project Summary", "")
    if not description: raise ValueError("Project Summary required")
    
    link = fields.get("Project Link", "")
    slug = slugify(title)
    
    raw_image = fields.get("Image", "")
    image = download_image(raw_image, slug, repo_root, "images/projects")
    if not image:
        image = "images/projects/photo.jpg"
    
    existing = load_projects(repo_root)
        
    new_project = {
        "title": title,
        "image": image,
        "link": link,
        "description": description
    }
    existing.append(new_project)
    
    save_projects(repo_root, existing)
    
    return {
        "action_type": "add-project",
        "item_name": title,
        "target_file": "_data/projects.yaml",
        "branch_name": f"add-project-{slug}",
        "pr_title": f"Add project: {title}"
    }


def process_remove_project(fields: dict, repo_root: Path) -> dict:
    title = fields.get("Project Name", "")
    if not title: raise ValueError("Project Name required")
    
    existing = load_projects(repo_root)
    if not existing:
        raise ValueError("projects.yaml is empty or not found")
        
    found = False
    for proj in existing:
        if proj.get("title", "").lower() == title.lower():
            proj["group"] = "previous"
            found = True
            break
            
    if not found:
        raise ValueError(f"Could not find project {title}")
        
    save_projects(repo_root, existing)
    
    slug = slugify(title)
    return {
        "action_type": "remove-project",
        "item_name": title,
        "target_file": "_data/projects.yaml",
        "branch_name": f"remove-project-{slug}",
        "pr_title": f"Remove project: {title}"
    }


def process_add_publication(fields: dict, repo_root: Path) -> dict:
    pub_id = fields.get("DOI or URL", "")
    if not pub_id: raise ValueError("DOI or URL required")
    
    title = fields.get("Title", "").strip()
    if not title: raise ValueError("Title required")
    
    # Ensure it starts with doi: or url: or some prefix
    if not (pub_id.startswith("doi:") or pub_id.startswith("url:") or pub_id.startswith("pmid:")):
        if pub_id.startswith("10."):
            pub_id = f"doi:{pub_id}"
        elif pub_id.startswith("http"):
            pub_id = f"url:{pub_id}"
            
    slug = slugify(title)
    safe_slug = slug[:40] if len(slug) > 40 else slug
    
    new_pub = {"id": pub_id, "title": title}
    
    if fields.get("Publisher"): new_pub["publisher"] = fields.get("Publisher")
    if fields.get("Date"): new_pub["date"] = fields.get("Date")
    if fields.get("Description"): new_pub["description"] = fields.get("Description")
    
    authors = fields.get("Authors", "")
    if authors:
        new_pub["authors"] = [a.strip() for a in authors.split(",") if a.strip()]
        
    sources_file = repo_root / "_data" / "sources.yaml"
    yaml = YAML()
    yaml.width = 4096
    yaml.default_flow_style = False
    
    sources = []
    if sources_file.exists():
        with open(sources_file, "r") as f:
            sources = yaml.load(f) or []
            
    sources.append(new_pub)
    
    buf = StringIO()
    yaml.dump(sources, buf)
    sources_file.write_text(buf.getvalue(), encoding="utf-8")
    
    return {
        "action_type": "add-publication",
        "item_name": title,
        "target_file": "_data/sources.yaml",
        "branch_name": f"add-publication-{safe_slug}",
        "pr_title": f"Add publication: {title}"
    }


def main():
    body = os.environ.get("ISSUE_BODY", "")
    title = os.environ.get("ISSUE_TITLE", "")
    number = os.environ.get("ISSUE_NUMBER", "0")
    repo_root = Path(os.environ.get("REPO_ROOT", ".")).resolve()

    if not body:
        print("::error::No ISSUE_BODY provided.")
        sys.exit(1)

    fields = parse_issue_form(body)

    try:
        if re.search(r"add\s*person", title, re.IGNORECASE):
            result = process_add_person(fields, repo_root)
        elif re.search(r"remove\s*person", title, re.IGNORECASE):
            result = process_remove_person(fields, repo_root)
        elif re.search(r"add\s*project", title, re.IGNORECASE):
            result = process_add_project(fields, repo_root)
        elif re.search(r"remove\s*project", title, re.IGNORECASE):
            result = process_remove_project(fields, repo_root)
        elif re.search(r"add\s*publication", title, re.IGNORECASE):
            result = process_add_publication(fields, repo_root)
        else:
            print(f"::error::Could not determine issue type from title: {title}")
            sys.exit(1)
    except Exception as e:
        print(f"::error::Error processing issue: {str(e)}")
        sys.exit(1)

    if number and number != "0":
        result["branch_name"] = f"{result['branch_name']}-{number}"

    result["created"] = "true"
    
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            for k, v in result.items():
                f.write(f"{k}={v}\n")

    print(f"Success: {result['pr_title']}")


if __name__ == "__main__":
    main()
