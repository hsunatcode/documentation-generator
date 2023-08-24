from langchain import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from dotenv import load_dotenv
import os
import ast

load_dotenv()


EXCLUDED_FILES = [
    ".env",
    ".gitignore",
    "alembic_config.py",
    "alembic.ini",
    "CODE_OF_CONDUCT.md",
]
EXCLUDED_PATH_PATTERNS = [
    "__pycache__/",
]
PROCESS_ONLY_PATHS = ["./app/"]


def extract_functions_from_code(code):
    """Extracts function code blocks from the given code."""
    tree = ast.parse(code)
    functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

    func_codes = []
    for func in functions:
        lines = code.splitlines()
        func_code = "\n".join(lines[func.lineno - 1 : func.end_lineno])
        func_codes.append(func_code)

    return func_codes


def is_excluded(file_path):
    """Check if the file or its path matches the exclude list."""
    unified_path = file_path.replace(os.sep, "/")

    if os.path.basename(unified_path) in EXCLUDED_FILES:
        return True

    for pattern in EXCLUDED_PATH_PATTERNS:
        if pattern in unified_path:
            return True

    for allowed_path in PROCESS_ONLY_PATHS:
        if unified_path.startswith(allowed_path):
            return False

    return True


def main():
    documentation_contents = "# Project Overview\n\n"

    for root, dirs, files in os.walk("."):
        print(f"Performing for {root} rn")
        for file in files:
            full_path = os.path.join(root, file)
            if file.endswith(".py") and not is_excluded(full_path):
                with open(full_path, "r") as f:
                    code = f.read()

                functions = extract_functions_from_code(code)
                if functions:
                    for function_code in functions:
                        try:
                            func_name = ast.parse(function_code).body[0].name
                        except Exception as e:
                            print(
                                f"Failed to extract function name from code: {function_code}. Error: {e}"
                            )
                            continue

                        doc = generate_code_documentation(function_code)
                        documentation_contents += f"### Function: {func_name}\n\n"
                        documentation_contents += f"#### Path: {full_path}\n\n"
                        documentation_contents += doc
                        documentation_contents += "\n\n"
                else:
                    doc = generate_code_documentation(code)
                    documentation_contents += f"## File: {file}\n\n"
                    documentation_contents += f"Path: {full_path}\n\n"
                    documentation_contents += doc
                    documentation_contents += "\n\n"
        print(f"Done with {root} rn")

    print("Writing the doc now")
    with open("documentation.md", "w") as f:
        f.write(documentation_contents)


def generate_code_documentation(code):
    documentation_template = """
        Take this code : {code} and Profile this in a detailed manner, Understand the data flows and how the code works in terms of logic.

        - Highligh the data flow of code. Keep it easy to read and concise.
        - Highlight the logic and how the code works in terms of logic. Keep is easy to read and consise.
        - for the tone : vary sentence length, be direct and to the point.
    """

    doc_prompt = PromptTemplate(
        input_variables=["code"],
        template=documentation_template,
    )

    llm = ChatOpenAI(temperature=0.9, model_name="gpt-3.5-turbo")
    chain = LLMChain(llm=llm, prompt=doc_prompt)
    return chain.run(code=code)


if __name__ == "__main__":
    main()
