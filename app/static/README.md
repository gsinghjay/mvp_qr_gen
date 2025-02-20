```mermaid
graph TB
    %% Explanatory Subgraphs at Top in a Row
    subgraph flow["How Static Files Work"]
        direction TB
        N1["(1) Browser requests page"]
        N2["(2) FastAPI returns HTML"]
        N3["(3) Browser sees static file links"]
        N4["(4) Browser requests each static file"]
        N5["(5) Static middleware serves files"]
        
        N1 --> N2 --> N3 --> N4 --> N5
    end

    subgraph purpose["Static Files Purpose"]
        direction TB
        P1["CSS: Styling and Layout"]
        P2["JavaScript: Interactivity"]
        P3["Assets: Images and Media"]
        P4["QR Codes: Generated Images"]
    end

    subgraph roles["JavaScript File Roles"]
        direction TB
        R1["api.js: Handle API calls"]
        R2["config.js: App configuration"]
        R3["script.js: Core functionality"]
        R4["utils.js: Helper functions"]
        R5["ui.js: User interface logic"]
    end

    %% Position subgraphs side by side
    flow --> purpose
    purpose --> roles

    %% Add some spacing
    spacer1[" "]
    spacer2[" "]
    roles --> spacer1
    spacer1 --> spacer2
    style spacer1 fill:none,stroke:none
    style spacer2 fill:none,stroke:none

    %% Main Flow Diagram Below Explanations
    spacer2 --> A
    
    %% Main User Flow
    A["User Browser"] --> B["FastAPI Application"]
    B --> C["Template Engine (Jinja2)"]
    C --> D["HTML Page"]
    D --> A

    %% Static Files Flow
    D -- "Requests static files" --> E["Static Files Middleware"]
    E -- "Serves" --> F["Static Files Directory (/app/static/)"]

    %% Static Directory Structure
    F --> G["CSS Directory (/css/)"]
    F --> H["JavaScript Directory (/js/)"]
    F --> I["Assets Directory (/assets/)"]
    F --> J["QR Codes Directory (/qr_codes/)"]

    %% CSS Details
    G --> G1["custom.css (Custom styling rules)"]
    G -.-> G2["Bootstrap CSS (External CDN)"]

    %% JavaScript Details
    H --> H1["api.js (API interactions)"]
    H --> H2["config.js (Configuration)"]
    H --> H3["script.js (Main logic)"]
    H --> H4["utils.js (Utility functions)"]
    H --> H5["ui.js (UI interactions)"]

    %% Assets Details
    I --> I1["images/ (Static images)"]

    %% QR Codes
    J --> J1["Generated QR codes"]

    %% Styling
    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#f9f,stroke:#333,stroke-width:2px
    style C fill:#cff,stroke:#333,stroke-width:2px
    style D fill:#cff,stroke:#333,stroke-width:2px
    style E fill:#ffc,stroke:#333,stroke-width:2px
    style F fill:#ccf,stroke:#333,stroke-width:2px
    
    %% Directory Styling
    style G fill:#e6e6ff,stroke:#333,stroke-width:1px
    style H fill:#e6e6ff,stroke:#333,stroke-width:1px
    style I fill:#e6e6ff,stroke:#333,stroke-width:1px
    style J fill:#e6e6ff,stroke:#333,stroke-width:1px

    %% File Styling
    style G1 fill:#fff,stroke:#333,stroke-width:1px
    style G2 fill:#fff,stroke:#333,stroke-width:1px,stroke-dasharray: 5 5
    style H1,H2,H3,H4,H5 fill:#fff,stroke:#333,stroke-width:1px
    style I1 fill:#fff,stroke:#333,stroke-width:1px
    style J1 fill:#fff,stroke:#333,stroke-width:1px

    %% Subgraph Styling
    style flow fill:#f5f5f5,stroke:#333,stroke-width:1px
    style purpose fill:#f5f5f5,stroke:#333,stroke-width:1px
    style roles fill:#f5f5f5,stroke:#333,stroke-width:1px
```

### Understanding Static Files in FastAPI

This diagram illustrates how static files work in our FastAPI application. Let's break it down for beginners:

#### What are Static Files?
Static files are files that don't change (remain "static") and are served directly to the browser. These include:
- CSS files (for styling)
- JavaScript files (for interactivity)
- Images (for visual content)
- Generated files (like QR codes in our case)

#### Directory Structure Explained
Our `/app/static/` directory contains:

1. **CSS Directory (`/css/`)**
   - `custom.css`: Our custom styling rules
   - We also use Bootstrap CSS (loaded from CDN) for consistent styling

2. **JavaScript Directory (`/js/`)**
   - `api.js`: Handles all API interactions with the backend
   - `config.js`: Contains application configuration
   - `script.js`: Main application logic
   - `utils.js`: Utility/helper functions
   - `ui.js`: User interface interactions

3. **Assets Directory (`/assets/`)**
   - `images/`: Static images used throughout the application

4. **QR Codes Directory (`/qr_codes/`)**
   - Stores generated QR code images

#### How It Works

1. **Initial Page Load**
   - User requests a page
   - FastAPI processes the request
   - Template engine (Jinja2) generates HTML
   - HTML is sent to the browser

2. **Static File Loading**
   - Browser reads HTML and finds links to static files
   - For each static file (CSS, JS, images):
     - Browser makes a new request
     - FastAPI's static middleware handles the request
     - File is served directly from the static directory

3. **File Types and Their Roles**
   - **CSS Files**: Control the appearance of the website
   - **JavaScript Files**: Add interactivity and functionality
   - **Images**: Provide visual content
   - **Generated Files**: Store dynamically created content (QR codes)

#### Best Practices
- Use `url_for('static', path='...')` in templates to link static files
- Keep files organized in appropriate subdirectories
- Use meaningful file names that indicate their purpose
- Minimize the number of static files to improve load times

This structure helps maintain a clean, organized, and efficient web application while making it easy to manage static content.