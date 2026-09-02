#!/usr/bin/env python3
import os
import tempfile
import unittest
from pathlib import Path
import yaml

from process_add_issue import (
    parse_issue_form,
    slugify,
    parse_links,
    categorize_role,
    process_person,
    process_project,
)


class TestProcessAddIssue(unittest.TestCase):

    def test_parse_issue_form(self):
        body = """
### Name

Jane Doe

### Affiliation

University of New Mexico

### Role

PhD Student

### Image

_No response_

### Email or links

jane@unm.edu, https://github.com/janedoe

### Notes

Jane is conducting HPC research.

### Checklist

- [X] I checked that this person does not already exist on the site.
"""
        fields = parse_issue_form(body)
        self.assertEqual(fields.get("Name"), "Jane Doe")
        self.assertEqual(fields.get("Affiliation"), "University of New Mexico")
        self.assertEqual(fields.get("Role"), "PhD Student")
        self.assertEqual(fields.get("Image"), "")  # Cleaned from _No response_
        self.assertEqual(fields.get("Email or links"), "jane@unm.edu, https://github.com/janedoe")
        self.assertEqual(fields.get("Notes"), "Jane is conducting HPC research.")

    def test_slugify(self):
        self.assertEqual(slugify("Jane Doe"), "jane-doe")
        self.assertEqual(slugify("John O'Connor-Smith"), "john-o-connor-smith")
        self.assertEqual(slugify("  Special @ Project #123! "), "special-project-123")

    def test_parse_links(self):
        raw = "dschafer1@unm.edu, 0000-0001-8438-5144, https://github.com/derek-schafer, https://example.com/me"
        links = parse_links(raw)
        self.assertEqual(links.get("email"), "dschafer1@unm.edu")
        self.assertEqual(links.get("orcid"), "0000-0001-8438-5144")
        self.assertEqual(links.get("github"), "derek-schafer")
        self.assertEqual(links.get("home-page"), "https://example.com/me")

    def test_categorize_role(self):
        self.assertEqual(categorize_role("Principal Investigator"), "principal-investigator")
        self.assertEqual(categorize_role("Co-PI"), "principal-investigator")
        self.assertEqual(categorize_role("PhD Student"), "student")
        self.assertEqual(categorize_role("Undergraduate Student"), "student")
        self.assertEqual(categorize_role("Administrative Coordinator"), "admin")
        self.assertEqual(categorize_role("Grant Manager"), "admin")
        self.assertEqual(categorize_role("Staff Research Scientist"), "programmer")
        self.assertEqual(categorize_role("Software Engineer"), "programmer")

    def test_process_person(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            fields = {
                "Name": "Jane Doe",
                "Affiliation": "University of New Mexico",
                "Role": "PhD Student",
                "Image": "images/jane-photo.jpg",
                "Email or links": "jane@unm.edu, https://orcid.org/0000-0002-1234-5678",
                "Notes": "Jane's research focuses on parallel task scheduling.",
            }
            res = process_person(fields, repo_root)
            self.assertEqual(res["action_type"], "person")
            self.assertEqual(res["target_file"], "_members/jane-doe.md")
            self.assertEqual(res["pr_title"], "Add person: Jane Doe")

            created_file = repo_root / "_members" / "jane-doe.md"
            self.assertTrue(created_file.exists())

            content = created_file.read_text(encoding="utf-8")
            parts = content.split("---")
            self.assertEqual(len(parts), 3)

            fm = yaml.safe_load(parts[1])
            self.assertEqual(fm["name"], "Jane Doe")
            self.assertEqual(fm["affiliation"], "University of New Mexico")
            self.assertEqual(fm["role"], "student")
            self.assertEqual(fm["description"], "PhD Student")
            self.assertEqual(fm["image"], "images/jane-photo.jpg")
            self.assertEqual(fm["links"]["email"], "jane@unm.edu")
            self.assertEqual(fm["links"]["orcid"], "0000-0002-1234-5678")

            body = parts[2].strip()
            self.assertEqual(body, "Jane's research focuses on parallel task scheduling.")

    def test_process_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            fields = {
                "Title": "New HPC Framework",
                "Subtitle": "A high-performance runtime",
                "Link": "https://hpc.example.org",
                "Repo": "COMPASS-PSAAP/hpc-framework",
                "Tags": "software, resource",
                "Image": "images/framework.png",
                "Short description": "High performance computing framework for PSAAP.",
            }
            res = process_project(fields, repo_root)
            self.assertEqual(res["action_type"], "project")
            self.assertEqual(res["target_file"], "_data/projects.yaml")
            self.assertEqual(res["pr_title"], "Add project: New HPC Framework")

            projects_file = repo_root / "_data" / "projects.yaml"
            self.assertTrue(projects_file.exists())

            data = yaml.safe_load(projects_file.read_text(encoding="utf-8"))
            self.assertEqual(len(data), 1)
            proj = data[0]
            self.assertEqual(proj["title"], "New HPC Framework")
            self.assertEqual(proj["subtitle"], "A high-performance runtime")
            self.assertEqual(proj["link"], "https://hpc.example.org")
            self.assertEqual(proj["repo"], "COMPASS-PSAAP/hpc-framework")
            self.assertEqual(proj["tags"], ["software", "resource"])
            self.assertEqual(proj["description"], "High performance computing framework for PSAAP.")

    def test_process_project_append_existing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            projects_file = repo_root / "_data" / "projects.yaml"
            projects_file.parent.mkdir(parents=True, exist_ok=True)
            initial_content = """- title: Existing Project
  description: Existing description
"""
            projects_file.write_text(initial_content, encoding="utf-8")

            fields = {
                "Title": "Second Project",
                "Short description": "Second description",
            }
            res = process_project(fields, repo_root)
            self.assertEqual(res["action_type"], "project")

            data = yaml.safe_load(projects_file.read_text(encoding="utf-8"))
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]["title"], "Existing Project")
            self.assertEqual(data[1]["title"], "Second Project")


if __name__ == "__main__":
    unittest.main()
