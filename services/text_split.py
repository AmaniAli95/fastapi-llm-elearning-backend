import os
import tempfile
import json
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain.document_loaders import UnstructuredMarkdownLoader

from db.database import log_job
from db.supabase import get_sb

def split_text(temp_file_path, headers_to_split_on,output_bucket_name,chapter_dir_path):
    loader = UnstructuredMarkdownLoader(temp_file_path)
    markdown_document = loader.load()
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    md_header_splits = markdown_splitter.split_text(markdown_document[0].page_content)
    for split in md_header_splits[1:]:
        header1 = split.metadata["Topik"]
        if not header1.strip().split()[0].isdigit():
            filename = f"{header1}.md"
            output_file_path = os.path.join(tempfile.gettempdir(), filename)
            with open(output_file_path, "w") as f:
                f.write(split.page_content)
            
            with open(output_file_path, "rb") as file:
                data = get_sb().storage.from_(output_bucket_name).upload(f"{chapter_dir_path}/{filename}", file)
            os.remove(output_file_path)
    return output_file_path

def generate_structure(temp_file_path):
    loader = UnstructuredMarkdownLoader(temp_file_path)
    markdown_document = loader.load()
    headers = [
        ("###", "Topic"),
        ("####", "Sub-Topic"),
        ("#####", "Sub-Sub-Topic")
    ]

    md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers)
    md_splits = md_splitter.split_text(markdown_document[0].page_content)

    structure_list = []
    parent_name = ""
    for split in md_splits:
        structure = {}
        if "Topic" in split.metadata:
            structure["Topic"] = split.metadata["Topic"]
            parent_name = split.metadata["Topic"]
        if "Sub-Topic" in split.metadata:
            if "Sub-Topic" not in structure:
                structure["Sub-Topic"] = {}
            structure["Sub-Topic"]["content"] = split.metadata["Sub-Topic"]
            parent_name = split.metadata["Sub-Topic"]
        if "Sub-Sub-Topic" in split.metadata:
            if "Sub-Topic" not in structure:
                structure["Sub-Topic"] = {}
            if "Sub-Sub-Topic" not in structure["Sub-Topic"]:
                structure["Sub-Topic"]["Sub-Sub-Topic"] = {}
            structure["Sub-Topic"]["Sub-Sub-Topic"]["content"] = split.metadata["Sub-Sub-Topic"]
            parent_name = structure["Sub-Topic"]["content"]
        structure["parent_name"] = parent_name
        structure_list.append(json.dumps(structure, indent=2))

    return ",\n".join(structure_list)
