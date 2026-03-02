"""
reset_project.py — Reset a project directory to a clean scaffold state.

Copies a template project (minus its src/ directory) to a target path,
then writes a minimal src/index.js and src/App.js stub. This is the
"clean slate" used before each game_coder iteration.
"""
import os
import shutil


def reset_project(
    target_dir: str,
    template_dir: str,
    stub_app_content: str | None = None,
) -> str:
    """
    Reset target_dir to a clean React scaffold based on template_dir.

    - Copies package.json, public/, and node_modules/ (symlinked to save
      space) from template_dir to target_dir.
    - Wipes target_dir/src/ and replaces it with a minimal stub.
    - Returns a short status string.
    """
    # Remove target if it exists, then recreate
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
    os.makedirs(target_dir)

    # Files/dirs to copy from template
    COPY_ITEMS = ["package.json", "package-lock.json", "public"]
    for item in COPY_ITEMS:
        src = os.path.join(template_dir, item)
        dst = os.path.join(target_dir, item)
        if not os.path.exists(src):
            continue
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

    # Symlink node_modules to avoid re-installing (saves minutes)
    nm_src = os.path.join(template_dir, "node_modules")
    nm_dst = os.path.join(target_dir, "node_modules")
    if os.path.isdir(nm_src):
        os.symlink(nm_src, nm_dst)

    # Write minimal src/
    src_dir = os.path.join(target_dir, "src")
    os.makedirs(src_dir)

    with open(os.path.join(src_dir, "index.js"), "w") as f:
        f.write(
            "import React from 'react';\n"
            "import ReactDOM from 'react-dom';\n"
            "import App from './App';\n\n"
            "ReactDOM.render(<App />, document.getElementById('root'));\n"
        )

    app_content = stub_app_content or (
        "import React from 'react';\n\n"
        "function App() {\n"
        "  return <div style={{ padding: 40 }}><h1>Photosynthesis</h1></div>;\n"
        "}\n\n"
        "export default App;\n"
    )
    with open(os.path.join(src_dir, "App.js"), "w") as f:
        f.write(app_content)

    return (
        f"Reset complete: {target_dir}\n"
        f"  Copied package.json, public/ from {template_dir}\n"
        f"  Symlinked node_modules\n"
        f"  Created src/index.js and src/App.js stubs"
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: reset_project.py <target_dir> <template_dir>")
        sys.exit(1)
    print(reset_project(sys.argv[1], sys.argv[2]))
