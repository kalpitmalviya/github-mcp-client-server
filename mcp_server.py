from mcp.server.fastmcp import FastMCP
from pydantic import Field
from mcp.server.fastmcp.prompts import base

mcp = FastMCP("DocumentMCP", log_level="ERROR")


docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}

@mcp.tool(
    name="read_doc_content",
    description="Read the content of a document and return a it as a string"
)
def read_doc_content(

    doc_id: str = Field(..., description="The ID of the document to read")
    ):
    
    if doc_id not in docs:
        raise ValueError(f'Document with ID {doc_id} not found.')

    return docs[doc_id]



@mcp.tool(
    name="edit_doc_content",
    description="Edit the a document by replacing a string in the document with a new string and return the updated content"
)
def edit_doc_content(
    doc_id: str = Field(..., description="The ID of the document to edit"),
    old_string: str = Field(..., description="The string to be replaced in the document"),
    new_string: str = Field(..., description="The string to replace the old string with in the document")
):
    if doc_id not in docs:
        raise ValueError(f'Document with ID {doc_id} not found.')

    content = docs[doc_id]
    updated_content = content.replace(old_string, new_string)
    docs[doc_id] = updated_content

    return updated_content



# TODO: Write a resource to return all doc id's
@mcp.resource(
    "docs://documents",
    mime_type="application/json",
    description="A resource that returns all document IDs available in the system"
)
def list_docs() -> list[str]:
    return list(docs.keys())

# TODO: Write a resource to return the contents of a particular doc
@mcp.resource(
    "docs://documents/{doc_id}",
    mime_type="text/plain",
    description="A resource that returns the content of a specific document by its ID"
)
def fetch_doc(doc_id: str) -> str:
    if doc_id not in docs:
        raise ValueError(f"Doc with ID {doc_id} not found.")
    return docs[doc_id]


# TODO: Write a prompt to rewrite a doc in markdown format
@mcp.prompt(
    name="formatt",
    description="Rewrite a document in markdown format"
)
def format_doc(
    doc_id: str = Field(..., description="The ID of the document to format")
) -> list[base.Message]:
    prompt = f"""
        Your goal is to reformat a document to be written with markdown syntax.

        The id of the document you need to reformat is:

        {doc_id}


        Add in headers, bullet points, tables, etc as necessary. Feel free to add in extra formatting.
        Use the 'edit_document' tool to edit the document. After the document has been reformatted...
    """
    
    return [
        base.UserMessage(prompt)
    ]





# TODO: Write a prompt to summarize a doc


if __name__ == "__main__":
    mcp.run(transport="stdio")