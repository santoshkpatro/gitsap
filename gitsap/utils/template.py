from django.conf import settings
from django.shortcuts import HttpResponse
import json

VITE_MANIFEST_PATH = settings.BASE_DIR / "dist" / ".vite" / "manifest.json"
VITE_DEV_SERVER = "http://localhost:5173"
DEBUG = settings.DEBUG

def get_vite_assets(manifest, entry_key, visited=None):
    """
    Recursively get all JS and CSS assets for a given entry point.
    Returns a tuple of (js_files, css_files) with proper loading order.
    """
    if visited is None:
        visited = set()
    
    if entry_key in visited or entry_key not in manifest:
        return [], []
    
    visited.add(entry_key)
    entry = manifest[entry_key]
    
    js_files = []
    css_files = []
    
    # First, process all imports recursively to maintain proper order
    if "imports" in entry:
        for import_key in entry["imports"]:
            import_js, import_css = get_vite_assets(manifest, import_key, visited)
            js_files.extend(import_js)
            css_files.extend(import_css)
    
    # Then add current entry's assets
    if "file" in entry:
        js_files.append(entry["file"])
    
    if "css" in entry:
        css_files.extend(entry["css"])
    
    return js_files, css_files

def vite_render(request, js_file, props={}):
    script_tags = []
    css_tags = []
    
    # For development, make sure Vite dev server is running on localhost:5173
    if DEBUG:
        vite_url = VITE_DEV_SERVER
        script_tags = [
            f'<script type="module" src="{vite_url}/@vite/client"></script>',
            f'<script type="module" src="{vite_url}{settings.STATIC_URL}{js_file}"></script>',
        ]
    else:
        with open(VITE_MANIFEST_PATH, "r") as f:
            manifest = json.load(f)
        
        key = f"static/{js_file}"
        if key in manifest:
            # Get all assets recursively
            js_files, css_files = get_vite_assets(manifest, key)
            
            # Create script tags in proper order (dependencies first)
            for js_file_path in js_files:
                script_tags.append(f'<script type="module" src="{settings.STATIC_URL}{js_file_path}"></script>')
            
            # Create CSS link tags (remove duplicates while preserving order)
            seen_css = set()
            for css_file in css_files:
                if css_file not in seen_css:
                    css_tags.append(f'<link rel="stylesheet" href="{settings.STATIC_URL}{css_file}">')
                    seen_css.add(css_file)
                    
        else:
            raise ValueError(f"{key} not found in Vite manifest")

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <link rel="icon" href="/static/favicon.ico" />
        <title>Vue Page</title>
        {''.join(css_tags)}
    </head>
    <body>
        <div id="app"></div>
        <script>
            // Pass props to your Vue component
            window.__PROPS__ = {json.dumps(props)};
        </script>
        {''.join(script_tags)}
    </body>
    </html>
    """
    return HttpResponse(html)